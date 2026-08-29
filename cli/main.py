import argparse

def main():
    parser = argparse.ArgumentParser(description="Ripple CLI - Impact analysis for code changes")
    parser.add_argument("--version", action="version", version="Ripple CLI v0.1.0")
    args = parser.parse_args()
    print("Ripple CLI initialized.")

if __name__ == "__main__":
    main()
