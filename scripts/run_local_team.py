import os
import sys

from core.ai.local_team import LocalAITeam


def main():
    if len(sys.argv) < 2:
        print("Kullanım: python scripts/run_local_team.py \"Görev metni\"")
        sys.exit(2)

    task = sys.argv[1]

    model = os.getenv("ANKA_OLLAMA_MODEL")
    base_url = os.getenv("ANKA_OLLAMA_URL")

    team = LocalAITeam(model=model, base_url=base_url)

    print("Servis sağlığı kontrol ediliyor...")
    if not team.health_check():
        print("Ollama servisine ulaşılamıyor. İşlem iptal edildi.")
        sys.exit(1)

    result = team.run(task)

    if not result.success:
        print("İş akışı başarısız:")
        for err in result.errors:
            print(" -", err)
        sys.exit(1)

    print("İş akışı başarıyla tamamlandı. Rol bazlı çıktılar:")
    for step in result.step_results:
        print(f"[{step.role}] {step.agent_name}: {step.output}")


if __name__ == "__main__":
    main()
