from search import answer_question


EXIT_COMMANDS = {"sair", "exit", "q"}


def main() -> None:
    print("Faca sua pergunta:")

    while True:
        question = input("> ").strip()

        if question.lower() in EXIT_COMMANDS:
            break

        if not question:
            continue

        answer = answer_question(question)
        print(f"PERGUNTA: {question}")
        print(f"RESPOSTA: {answer}")


if __name__ == "__main__":
    main()
