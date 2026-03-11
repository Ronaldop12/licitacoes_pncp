"""Entrypoint para executar o agendador como serviço standalone."""
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    from agendador import AgendadorTarefas

    logger.info("Iniciando serviço agendador...")
    ag = AgendadorTarefas()
    ag.iniciar()
    logger.info("Agendador ativo. Jobs: %s", [j["id"] for j in ag.listar_jobs()])

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        ag.parar()
        logger.info("Agendador encerrado.")
