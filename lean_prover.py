import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are an expert in propositional logic and LEAN theorem prover.

Your objectives are:
1. Generate formal proofs in LEAN 3 for valid arguments
2. Generate valid counterexamples for invalid arguments

LEAN 3 FORMAT (based on https://leanprover.github.io/logic_and_proof_lean3/natural_deduction_for_propositional_logic.html):

For VALID proofs, use:
```lean
theorem proof (p q r : Prop) : conclusion := by
  intro
  -- Use tactics: exact, apply, have, cases, contradiction, etc.
  sorry
```

For COUNTEREXAMPLES, describe a truth assignment that falsifies the argument:
```
Counterexample:
p = true
q = false
r = true
...
```

Be concise and direct. Always explain the logic used."""

COUNTEREXAMPLE_PROMPT_WITH_GUIDANCE = """You are an expert in propositional logic.

To validate a counterexample:
1. Check that ALL premises are TRUE under the assignment
2. Check that the CONCLUSION is FALSE under the assignment
3. If both conditions are met, the counterexample is VALID

Present in this exact format:
Counterexample:
p = [true/false]
q = [true/false]
...

Verification:
- Premise 1: [formula] = [true/false]
- Premise 2: [formula] = [true/false]
- Conclusion: [formula] = [true/false]

Status: VALID/INVALID counterexample"""

COUNTEREXAMPLE_PROMPT_WITHOUT_GUIDANCE = """Generate a counterexample for the following argument:

p = [true/false]
q = [true/false]
..."""

def generate_lean_proof(propositions: list[str], premises: list[str], conclusion: str) -> str:
    propositions_str = " ".join(f"({prop} : Prop)" for prop in propositions)

    prompt = f"""Generate a LEAN proof for the following valid argument:

Propositions: {propositions_str}

Premises:
{chr(10).join(f'  {i+1}. {p}' for i, p in enumerate(premises))}

Conclusion: {conclusion}

Generate the corresponding LEAN code using natural deduction."""

    model = genai.GenerativeModel("gemini-2.0-flash", system_instruction=SYSTEM_PROMPT)
    response = model.generate_content(prompt)

    return response.text

def generate_counterexample(propositions: list[str], premises: list[str], conclusion: str) -> str:
    prompt = f"""Generate a counterexample for the following INVALID argument:

Propositions: {", ".join(propositions)}

Premises:
{chr(10).join(f'  {i+1}. {p}' for i, p in enumerate(premises))}

Conclusion: {conclusion}

Show a truth assignment that makes ALL premises true but the conclusion FALSE.
Format:
p = true
q = false
...

Explain why this is a valid counterexample."""

    model = genai.GenerativeModel("gemini-2.0-flash", system_instruction=SYSTEM_PROMPT)
    response = model.generate_content(prompt)

    return response.text

def generate_counterexample_with_guidance(propositions: list[str], premises: list[str], conclusion: str) -> str:
    propositions_str = ", ".join(propositions)

    prompt = f"""Generate a counterexample for the following INVALID argument:

Propositions: {propositions_str}

Premises:
{chr(10).join(f'  {i+1}. {p}' for i, p in enumerate(premises))}

Conclusion: {conclusion}

IMPORTANT VERIFICATION RULES:
1. Find a truth assignment where ALL premises evaluate to TRUE
2. The CONCLUSION must evaluate to FALSE with this assignment
3. Verify each premise and the conclusion
4. If the assignment violates these rules, it is NOT a valid counterexample

Present in this exact format:
Counterexample:
[assignments]

Verification:
[Show each premise and conclusion evaluation]

Status: VALID or INVALID"""

    model = genai.GenerativeModel("gemini-2.0-flash", system_instruction=SYSTEM_PROMPT)
    response = model.generate_content(prompt)
    return response.text

def generate_counterexample_without_guidance(propositions: list[str], premises: list[str], conclusion: str) -> str:
    propositions_str = ", ".join(propositions)

    prompt = f"""Propositions: {propositions_str}

Premises:
{chr(10).join(f'  {i+1}. {p}' for i, p in enumerate(premises))}

Conclusion: {conclusion}

Counterexample:"""

    model = genai.GenerativeModel("gemini-2.0-flash", system_instruction=SYSTEM_PROMPT)
    response = model.generate_content(prompt)
    return response.text

def validate_lean_proof(proof: str) -> bool:
    checks = [
        "theorem" in proof or "lemma" in proof,
        ":=" in proof or ":= by" in proof,
    ]
    return all(checks)

def validate_counterexample(counterexample: str) -> bool:
    checks = [
        "=" in counterexample,
        any(keyword in counterexample.lower() for keyword in ["true", "false"]),
    ]
    return all(checks)

def compare_counterexamples(propositions: list[str], premises: list[str], conclusion: str) -> dict:
    result = {}

    try:
        without_guidance = generate_counterexample_without_guidance(propositions, premises, conclusion)
        result['without_guidance'] = {
            'counterexample': without_guidance,
            'valid': validate_counterexample(without_guidance)
        }
    except Exception as e:
        result['without_guidance'] = {'error': str(e), 'valid': False}

    try:
        with_guidance = generate_counterexample_with_guidance(propositions, premises, conclusion)
        result['with_guidance'] = {
            'counterexample': with_guidance,
            'valid': validate_counterexample(with_guidance)
        }
    except Exception as e:
        result['with_guidance'] = {'error': str(e), 'valid': False}

    return result

def generate_lean_proof_without_guidance(propositions: list[str], premises: list[str], conclusion: str) -> str:
    propositions_str = " ".join(f"({prop} : Prop)" for prop in propositions)

    prompt = f"""Generate a LEAN proof for the following valid argument WITHOUT explanation:

Propositions: {propositions_str}

Premises:
{chr(10).join(f'  {i+1}. {p}' for i, p in enumerate(premises))}

Conclusion: {conclusion}

Just provide the LEAN code, nothing else."""

    model = genai.GenerativeModel("gemini-2.0-flash", system_instruction=SYSTEM_PROMPT)
    response = model.generate_content(prompt)
    return response.text

def compare_with_and_without_guidance(propositions: list[str], premises: list[str], conclusion: str) -> dict:
    result = {}

    try:
        without_guidance = generate_lean_proof_without_guidance(propositions, premises, conclusion)
        result['without_guidance'] = {
            'proof': without_guidance,
            'valid': validate_lean_proof(without_guidance)
        }
    except Exception as e:
        result['without_guidance'] = {'error': str(e), 'valid': False}

    try:
        with_guidance = generate_lean_proof(propositions, premises, conclusion)
        result['with_guidance'] = {
            'proof': with_guidance,
            'valid': validate_lean_proof(with_guidance)
        }
    except Exception as e:
        result['with_guidance'] = {'error': str(e), 'valid': False}

    return result

def interactive_conversation() -> None:
    model = genai.GenerativeModel("gemini-2.0-flash", system_instruction=SYSTEM_PROMPT)
    chat = model.start_chat()

    print("\nModo Conversacional - Digite 'sair' para encerrar")
    print("=" * 60)

    while True:
        user_input = input("\nVocê: ").strip()

        if user_input.lower() == "sair":
            break

        response = chat.send_message(user_input)
        print(f"\nGemini: {response.text}")

if __name__ == "__main__":
    print("Teste - Gerando prova para Modus Ponens...")
    print("=" * 60)

    proof = generate_lean_proof(
        propositions=["p", "q"],
        premises=["p", "p → q"],
        conclusion="q"
    )

    print("\nProva gerada:")
    print(proof)
    print("\nVálida?" if validate_lean_proof(proof) else "\nInválida?")

