import logging
import structlog


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.ExceptionRenderer(),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True, # Set to False
    ) 
    
    # logging.getLogger("discord.voice_client").setLevel(logging.ERROR)
    # logging.getLogger("urllib3").setLevel(logging.WARNING)
    # logging.getLogger("requests").setLevel(logging.WARNING)
    # logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
    # logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
