import json
from dataclasses import asdict, dataclass
from pathlib import Path

from openai import OpenAI
from openai.types.chat import ChatCompletion

from errors import ContextParsingError, UnexpectedGptResponse
from stubs import (
    GetOrdersRequest,
    GetPnlRequest,
    MetricWindow,
    NullRequest,
    OrderSide,
    OrderType,
    Request,
    SubmitTradeRequest,
)


ALLOWED_EVAL_OBJECTS: dict[str, type] = {
    "NullRequest": NullRequest,
    "GetOrdersRequest": GetOrdersRequest,
    "GetPnlRequest": GetPnlRequest,
    "SubmitTradeRequest": SubmitTradeRequest,
    "OrderSide": OrderSide,
    "OrderType": OrderType,
    "MetricWindow": MetricWindow,
}

PROMPT_RESOLVE: str = "RESOLVE"
PROMPT_INIT_MESSAGE: str = "INIT"
PROMPT_RAND_MESSAGE: str = "RAND"
PROMPT_ERR_MESSAGE: str = "ERR"

CONTEXT_ROOT: Path = Path.cwd().parent / "context"
SYSTEM_CONTEXT: str = f"""
You are a character named {{name}}. You only respond to these commands:
1. {PROMPT_RESOLVE} $input -> request|text
    - request: valid Python object that will be passed into `eval()`. Constructed using $input.
        - One of:
            - NullRequest()
            - GetOrdersRequest(window=MetricWindow)
            - GetPnlRequest(window=MetricWindow)
            - SubmitTradeRequest(symbol=str, qty=float, side=OrderSide, type=OrderType)
        - Enums:
            - OrderSide: has options {[x.name for x in OrderSide]}
            - OrderType: has options {[x.name for x in OrderType]}
            - MetricWindow: has options {[x.name for x in MetricWindow]}
    - text: commentary based on input and context details
2. {PROMPT_INIT_MESSAGE} -> NullRequest()|text
    - text: character-specific greeting. State your name as well
3. {PROMPT_RAND_MESSAGE} -> NullRequest()|text
    - text: random character-specific phrase. Make this a truly random phrase that is unique
4. {PROMPT_ERR_MESSAGE} -> NullRequest()|text
    - text: character-specific message stating some error occurred

Context details:
{{details}}

Examples:
{{examples}}
"""


@dataclass(kw_only=True)
class GptInput:
    role: str
    content: str


@dataclass(kw_only=True)
class GptOutput:
    request: Request
    text: str | None

    @classmethod
    def from_response(cls, resp: ChatCompletion) -> "GptOutput":
        try:
            raw: str = resp.choices[0].message.content
            request_repr, text = raw.split("|")
            return cls(
                request=eval(request_repr, ALLOWED_EVAL_OBJECTS),
                text=None if text == "None" else text,
            )
        except Exception:
            raise UnexpectedGptResponse(raw)


class LlmCharacter:
    def __init__(
        self, name: str, openai_api_key: str, model: str, temperature: float
    ) -> None:
        self.name: str = name
        self.client: OpenAI = OpenAI(api_key=openai_api_key)
        self.model: str = model
        self.temperature: float = temperature
        self.context: GptInput = self._create_context(name)

    @staticmethod
    def _create_context(name: str) -> GptInput:
        context_path: Path = CONTEXT_ROOT / f"{name}.json"
        if not context_path.exists():
            raise FileNotFoundError(
                f"Missing required character context at {context_path}"
            )

        try:
            with open(context_path, "r") as f:
                context: dict = json.loads(f.read())
            assert "details" in context, "Context JSON must contain character details"
            assert "examples" in context, "Context JSON must contain example calls"
        except Exception as e:
            raise ContextParsingError(str(e))

        return GptInput(
            role="system",
            content=SYSTEM_CONTEXT.format(
                name=name, details=context["details"], examples=context["examples"]
            ),
        )

    def _prompt_gpt(self, prompt: str) -> GptOutput:
        messages: tuple[GptInput] = (
            self.context,
            GptInput(role="user", content=prompt),
        )
        resp: ChatCompletion = self.client.chat.completions.create(
            messages=[asdict(m) for m in messages],
            model=self.model,
            temperature=self.temperature,
        )
        return GptOutput.from_response(resp)

    def resolve(self, input_message: str) -> tuple[Request, str | None]:
        input_message: str = input_message.lower()
        if self.name not in input_message:
            return NullRequest(), None

        prompt: str = f"{PROMPT_RESOLVE}: {input_message}"
        output: GptOutput = self._prompt_gpt(prompt)
        return output.request, output.text

    def get_init_message(self) -> str:
        output: GptOutput = self._prompt_gpt(PROMPT_INIT_MESSAGE)
        return output.text

    def get_random_phrase(self) -> str:
        output: GptOutput = self._prompt_gpt(PROMPT_RAND_MESSAGE)
        return output.text

    def get_error_message(self) -> str:
        output: GptOutput = self._prompt_gpt(PROMPT_ERR_MESSAGE)
        return output.text
