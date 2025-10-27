from data_loader import load_data
from question_parser import parse_question
from query_engine import get_wage
from response_generator import generate_response

class Chatbot:
    def __init__(self):
        self.data = load_data()

    def ask(self, question):
        parsed = parse_question(question)
        if parsed["intent"] == "wage_lookup":
            result = get_wage(self.data, parsed["state"], parsed["year"], parsed["tipped"])
            return generate_response(result, parsed["state"], parsed["year"], parsed["tipped"])
        else:
            return "Desculpe, não entendi sua pergunta."
