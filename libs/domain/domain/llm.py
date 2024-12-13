from enum import Enum


class LLMProvider(str, Enum):
    ANTHROPIC = "ANTHROPIC"
    OLLAMA = "OLLAMA"


class LLMModel(str, Enum):
    CLAUDE_3_5_SONNET_20240620 = "claude-3-5-sonnet-20240620"
    LLAMA_3_2_3B = "llama3.2:3b"
