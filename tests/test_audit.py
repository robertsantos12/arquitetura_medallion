import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from medallion.config import PipelineConfig
from medallion.observability.audit import AuditPersistenceError, AuditRun, serializar, verificar_arquivos


class MemorySink:
    def __init__(self, falhar_em=None):
        self.registros = []
        self.falhar_em = falhar_em

    def append(self, evento, arquivo, digest):
        if evento["status"] == self.falhar_em:
            raise OSError("Falha simulada do destino Delta")
        self.registros.append({"event_id": evento["event_id"], "arquivo": arquivo,
                               "arquivo_sha256": digest, "payload_json": serializar(evento).decode()})


class AuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def nova(self, sink=None):
        return AuditRun(self.tmp.name, sink or MemorySink(), PipelineConfig(batch_id="lote_1"),
                        "teste", {"src/exemplo.py": "resultado = 4\n"})

    def test_sucesso_releitura_sem_estado_da_execucao(self):
        run = self.nova()
        run.executar(lambda ctx: ctx.verificar("resultado", 4, 4))
        # Reconstituir a consulta apenas com dados serializados e arquivos.
        registros = json.loads(json.dumps(run.sink.registros))
        resultado = verificar_arquivos(registros)
        self.assertEqual(resultado["status"], "SUCESSO")
        self.assertEqual(resultado["eventos"], 3)
        self.assertTrue(resultado["hashes_verificados"])

    def test_mesmo_lote_preserva_duas_tentativas(self):
        a, b = self.nova(), self.nova()
        for run in (a, b):
            run.executar(lambda ctx: ctx.verificar("resultado", 1, 1))
        self.assertNotEqual(a.run_id, b.run_id)
        self.assertTrue(a.pasta.exists() and b.pasta.exists())
        self.assertEqual(a.contexto["batch_id"], b.contexto["batch_id"])

    def test_erro_preservado_e_propagado(self):
        run = self.nova()
        with self.assertRaisesRegex(AssertionError, "resultado"):
            run.executar(lambda ctx: ctx.verificar("resultado", 1, 2))
        self.assertEqual(verificar_arquivos(run.sink.registros)["status"], "FALHOU")
        erro = json.loads(run.sink.registros[-1]["payload_json"])
        self.assertIn("AssertionError", erro["detalhes"]["traceback"])

    def test_falha_no_arquivo_impede_sucesso(self):
        run = self.nova(MemorySink(falhar_em="SUCESSO"))
        with self.assertRaises(AuditPersistenceError):
            run.executar(lambda ctx: ctx.verificar("resultado", 1, 1))
        self.assertEqual(verificar_arquivos(run.sink.registros)["status"], "SEM_CONCLUSAO")
        self.assertFalse(run.finalizado)

    def test_falha_no_registro_do_erro_preserva_causa(self):
        run = self.nova(MemorySink(falhar_em="FALHOU"))
        with self.assertRaises(AuditPersistenceError) as raised:
            run.executar(lambda ctx: ctx.verificar("resultado", 1, 2))
        self.assertIsInstance(raised.exception.__cause__, AssertionError)

    def test_arquivo_corrompido_detectado(self):
        run = self.nova()
        run.executar(lambda ctx: ctx.verificar("resultado", 1, 1))
        Path(run.sink.registros[-1]["arquivo"]).write_text("{}")
        with self.assertRaisesRegex(ValueError, "Hash divergente"):
            verificar_arquivos(run.sink.registros)

    def test_snapshot_de_codigo_corrompido_detectado(self):
        run = self.nova()
        run.executar(lambda ctx: ctx.verificar("resultado", 1, 1))
        (run.pasta / "fontes.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "Artefato anterior"):
            verificar_arquivos(run.sink.registros)

    def test_eventos_duplicados_ou_ausentes_detectados(self):
        run = self.nova()
        run.executar(lambda ctx: ctx.verificar("resultado", 1, 1))
        for registros in (run.sink.registros + [run.sink.registros[-1]], run.sink.registros[1:]):
            with self.subTest(registros=len(registros)), self.assertRaises(ValueError):
                verificar_arquivos(registros)

    def test_sem_check_nao_e_sucesso(self):
        run = self.nova()
        with self.assertRaisesRegex(ValueError, "sem verificações"):
            run.executar(lambda ctx: None)
        self.assertEqual(verificar_arquivos(run.sink.registros)["status"], "FALHOU")

    def test_interrupcao_nao_e_convertida_em_sucesso(self):
        run = self.nova()

        def interromper(ctx):
            raise KeyboardInterrupt()

        with self.assertRaises(KeyboardInterrupt):
            run.executar(interromper)
        self.assertEqual(verificar_arquivos(run.sink.registros)["status"], "SEM_CONCLUSAO")


if __name__ == "__main__":
    unittest.main()
