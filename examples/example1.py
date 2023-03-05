import feste
from feste.backend import Cohere, OpenAI
from feste.prompt import Prompt


def main() -> None:
    prompt = Prompt("Your name is SmartChat and you are an assistant."
                    " You should answer the following question: {{question}}")
    open_ai_api = OpenAI("[api key]")
    cohere_api = Cohere("[api key]")

    p1 = open_ai_api.complete(prompt(question="What is your name?"))
    p2 = open_ai_api.complete(prompt(question="Who are you?"))
    p3 = cohere_api.generate(prompt(question="What is your name?"))

    m = prompt(question=p3)

    results = feste.compute([p1, p2, p3, m])
    print(results)


if __name__ == "__main__":
    main()
