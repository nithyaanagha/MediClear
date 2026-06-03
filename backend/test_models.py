import os

from dotenv import load_dotenv


def main():
    load_dotenv()

    try:
        from doctr.models import ocr_predictor
    except Exception as exc:
        print("docTR import failed")
        print(exc)
        return

    print("docTR import OK")

    try:
        ocr_predictor(pretrained=False)
        print("docTR predictor construction OK")
    except Exception as exc:
        print("docTR predictor construction failed")
        print(exc)

    if os.getenv("GROQ_API_KEY"):
        print("GROQ_API_KEY configured")
    else:
        print("GROQ_API_KEY missing")


if __name__ == "__main__":
    main()
