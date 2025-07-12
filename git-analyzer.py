import os
import shutil
import datetime
import subprocess
import tempfile
import random
import configparser
import argparse


def analyze_real_git_commits(
    repo_urls: list[str], company_identifier: str, months_back: int
) -> dict:
    """
    Clones Git repositories, finds commits by a specified company within a timeframe,
    and returns structured commit data.

    Args:
        repo_urls: A list of Git repository URLs.
        company_identifier: A string to identify company commits (e.g., email domain or part of the committer name).
        months_back: An integer representing the number of months to look back for commits.

    Returns:
        A dictionary containing the structured commit data or an error message.
    """
    temp_dir = None
    all_repo_commits_structured = []

    try:
        # Check if Git command is available
        try:
            subprocess.run(
                ["git", "--version"], check=True, capture_output=True, text=True
            )
        except FileNotFoundError:
            return {
                "error": "Git command not found. Please ensure Git is installed and in your system's PATH."
            }
        except subprocess.CalledProcessError as e:
            return {"error": f"Error checking Git version: {e.stderr.decode().strip()}"}
        except Exception as e:
            return {
                "error": f"An unexpected error occurred during Git version check: {str(e)}"
            }

        temp_dir = tempfile.mkdtemp()

        # Calculate the 'since' date for git log
        since_date = (
            datetime.datetime.now() - datetime.timedelta(days=months_back * 30)
        ).strftime("%Y-%m-%d %H:%M:%S")

        for repo_url in repo_urls:
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            repo_path = os.path.join(temp_dir, repo_name)

            print(f"Cloning {repo_url} into {repo_path}...")
            try:
                # Clone the repository
                subprocess.run(
                    ["git", "clone", "--quiet", repo_url, repo_path],
                    check=True,
                    capture_output=True,
                )
                print(f"Successfully cloned {repo_name}.")
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode().strip()
                print(f"Error cloning repository {repo_url}: {error_msg}")
                all_repo_commits_structured.append(
                    {
                        "repo_name": repo_name,
                        "repo_url": repo_url,
                        "error": f"Failed to clone: {error_msg}",
                        "commits": [],  # No commits if clone failed
                    }
                )
                continue  # Skip to next repository
            except Exception as e:
                print(
                    f"An unexpected error occurred during cloning {repo_url}: {str(e)}"
                )
                all_repo_commits_structured.append(
                    {
                        "repo_name": repo_name,
                        "repo_url": repo_url,
                        "error": f"An unexpected error occurred during cloning: {str(e)}",
                        "commits": [],
                    }
                )
                continue

            print(f"Analyzing commits for {repo_name} since {since_date}...")
            try:
                # Get commit logs, formatted for easy parsing
                # --no-merges to exclude merge commits for cleaner summaries
                git_log_command = [
                    "git",
                    "-C",
                    repo_path,
                    "log",
                    f'--since="{since_date}"',
                    "--pretty=format:%H%n%an%n%ae%n%ad%n%s%n---END-COMMIT---",
                    "--date=iso",
                ]
                result = subprocess.run(
                    git_log_command,
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                )
                commits_raw = result.stdout.strip().split("---END-COMMIT---")

                repo_commits_list = []
                for commit_block in commits_raw:
                    if not commit_block.strip():
                        continue
                    parts = commit_block.strip().split("\n")
                    if len(parts) >= 5:
                        commit_hash = parts[0]
                        author_name = parts[1]
                        author_email = parts[2]
                        commit_date = parts[3]
                        commit_message = "\n".join(parts[4:]).strip()

                        # Filter by company identifier (case-insensitive)
                        if (
                            company_identifier.lower() in author_name.lower()
                            or company_identifier.lower() in author_email.lower()
                        ):
                            repo_commits_list.append(
                                {
                                    "hash": commit_hash,
                                    "author_name": author_name,
                                    "author_email": author_email,
                                    "date": commit_date,
                                    "message": commit_message,
                                }
                            )

                all_repo_commits_structured.append(
                    {
                        "repo_name": repo_name,
                        "repo_url": repo_url,
                        "commits": repo_commits_list,
                    }
                )

            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode().strip()
                print(f"Error getting git log for {repo_name}: {error_msg}")
                all_repo_commits_structured.append(
                    {
                        "repo_name": repo_name,
                        "repo_url": repo_url,
                        "error": f"Failed to get commit log: {error_msg}",
                        "commits": [],
                    }
                )
            except Exception as e:
                print(f"Error processing commits for {repo_name}: {e}")
                all_repo_commits_structured.append(
                    {
                        "repo_name": repo_name,
                        "repo_url": repo_url,
                        "error": f"Error processing commits: {str(e)}",
                        "commits": [],
                    }
                )

        return {
            "commit_data": all_repo_commits_structured,
            "message": "Commit analysis complete.",
        }

    except Exception as e:
        print(f"An unexpected error occurred in analyze_real_git_commits: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}"}
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")


def generate_article_content(commit_data: list[dict], months_back: int) -> str:
    """
    Generates a blog article based on commit data.
    In a real tool, this would call a large language model API (e.g., Gemini).

    Args:
        commit_data: Structured commit data.
        months_back: The number of months the analysis covered.

    Returns:
        A string containing the blog article.
    """
    if not commit_data:
        return "No relevant commits found to generate an article."

    # This is where you would integrate with a real LLM API.
    # For demonstration, we'll generate the article directly from the data.
    # To use Gemini, you'd replace this section with a call to its API.
    # Example (conceptual):
    # from google.generativeai import GenerativeModel
    # model = GenerativeModel(model_name="gemini-2.0-flash")
    # prompt = f"Generate a blog article summarizing recent Git commits... Here is the data: {json.dumps(commit_data)}"
    # response = model.generate_content(prompt)
    # return response.text

    article_content = f"""
# Recent Developments: A Look at Our Codebase ({months_back} Months Review)

We're excited to share a summary of the significant progress made across our repositories in the last {months_back} months. Our dedicated team has been busy pushing new features, refining existing functionalities, and enhancing the overall stability of our products.

Here's a breakdown of key contributions by repository:

"""

    for repo in commit_data:
        article_content += f"## {repo['repo_name']}\n"
        article_content += f"Repository URL: {repo['repo_url']}\n\n"

        if "error" in repo:
            article_content += (
                f"**Error processing this repository:** {repo['error']}\n\n"
            )
        elif repo["commits"]:
            article_content += "Our team has made the following notable commits:\n\n"
            for commit in repo["commits"]:
                # Ensure the message is handled, even if it's empty or malformed
                first_line_message = (
                    commit["message"].split("\n")[0]
                    if commit["message"]
                    else "(No message)"
                )
                first_line_message = first_line_message.replace("_", r"\_")
                article_content += f"- **{commit['author_name']}** on {commit['date'].split('T')[0]}: {first_line_message}\n"
            article_content += "\n"
        else:
            article_content += f"No company-specific commits were identified in this repository during the last {months_back} months.\n\n"

    article_content += """
This overview highlights the continuous effort and innovation from our development team. We look forward to bringing even more exciting updates in the future!

---
*Generated by the Git Commit Article Generator*
"""
    return article_content


def load_config_from_ini(file_path: str) -> dict | None:
    """
    Loads configuration from an INI file.

    Args:
        file_path: The path to the INI configuration file.

    Returns:
        A dictionary containing the configuration, or None if the file cannot be read.
    """
    config = configparser.ConfigParser()
    try:
        config.read(file_path)
        git_config = {}
        if "GitConfig" in config:
            repo_urls_str = config["GitConfig"].get("repo_urls", "")
            git_config["repo_urls"] = [
                url.strip() for url in repo_urls_str.split(",") if url.strip()
            ]
            git_config["company_identifier"] = (
                config["GitConfig"].get("company_identifier", "").strip()
            )
            git_config["months_back"] = config["GitConfig"].getint("months_back", None)
        return git_config
    except Exception as e:
        print(f"Error reading INI file {file_path}: {e}")
        return None


def main():
    """
    Main function to run the Git commit analysis and article generation tool.
    Supports optional configuration from an INI file and command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Generate a blog article summarizing Git commits from repositories."
    )
    parser.add_argument(
        "-r",
        "--repo-urls",
        help="Comma-separated list of Git repository URLs.",
        type=str,
    )
    parser.add_argument(
        "-c",
        "--company-identifier",
        help='String to identify company commits (e.g., email domain or "My Company Name").',
        type=str,
    )
    parser.add_argument(
        "-m",
        "--months-back",
        help="Number of months back to analyze commits.",
        type=int,
    )
    parser.add_argument(
        "-f",
        "--config-file",
        help="Path to an INI configuration file. If provided and successfully loaded, it will override other core parameters (-r, -c, -m).",
        type=str,
    )
    parser.add_argument(
        "-s",
        "--save-to-file",
        help="Automatically save the generated article to a file (provide filename).",
        type=str,
        nargs="?",  # Allows the argument to be optional, if present without value, it's None
        const="git_report.md",  # Default value if -s is present without an argument
    )

    args = parser.parse_args()

    repo_urls = []
    company_identifier = ""
    months_back = None
    save_file_name = None

    config_loaded_successfully = False

    # Attempt to load from INI file if specified
    if args.config_file:
        config_data = load_config_from_ini(args.config_file)
        if config_data:
            repo_urls = config_data.get("repo_urls", [])
            company_identifier = config_data.get("company_identifier", "")
            months_back = config_data.get("months_back", None)
            config_loaded_successfully = True
            print(f"Configuration loaded from {args.config_file}.")
        else:
            print(
                f"Warning: Failed to load configuration from {args.config_file}. Proceeding with command-line arguments or prompts."
            )

    # If config file was NOT successfully loaded, or not provided, then use CLI args
    if not config_loaded_successfully:
        if args.repo_urls:
            repo_urls = [
                url.strip() for url in args.repo_urls.split(",") if url.strip()
            ]
        if args.company_identifier:
            company_identifier = args.company_identifier.strip()
        if args.months_back is not None:
            months_back = args.months_back

    # The save_to_file argument always takes precedence from CLI
    if args.save_to_file is not None:
        save_file_name = args.save_to_file

    # 3. Prompt for missing values (lowest priority)
    if not repo_urls:
        repo_urls_input = input(
            "Enter Git repository URLs (comma-separated, e.g., https://github.com/org/repo1.git,https://github.com/org/repo2.git): "
        ).strip()
        repo_urls = [url.strip() for url in repo_urls_input.split(",") if url.strip()]

    if not repo_urls:
        print("No repository URLs provided. Exiting.")
        return

    if not company_identifier:
        company_identifier = input(
            "Enter your company identifier (e.g., @mycompany.com or 'My Company Name'): "
        ).strip()

    if not company_identifier:
        print("Company identifier cannot be empty. Exiting.")
        return

    if months_back is None:
        while True:
            try:
                months_back = int(
                    input("Enter number of months back to analyze (e.g., 3): ").strip()
                )
                if months_back <= 0:
                    raise ValueError
                break
            except ValueError:
                print("Invalid input. Please enter a positive integer for months.")

    print("\nStarting real Git analysis...")
    # Step 1: Perform real Git commit analysis
    analysis_result = analyze_real_git_commits(
        repo_urls, company_identifier, months_back
    )

    if "error" in analysis_result:
        print(f"\nError during Git analysis: {analysis_result['error']}")
        return

    commit_data = analysis_result.get("commit_data", [])

    # Step 2: Generate article content
    article = generate_article_content(commit_data, months_back)

    print("\n--- Generated Article ---")
    print(article)
    print("\n--- End of Article ---")

    # Handle saving to file based on CLI arg or prompt
    if save_file_name:
        try:
            with open(save_file_name, "w", encoding="utf-8") as f:
                f.write(article)
            print(f"Article automatically saved to {save_file_name}")
        except Exception as e:
            print(f"Error automatically saving file {save_file_name}: {e}")
    else:
        save_option = (
            input("\nDo you want to save the article to a file? (yes/no): ")
            .lower()
            .strip()
        )
        if save_option == "yes":
            file_name = input("Enter desired filename (e.g., git_report.md): ").strip()
            if not file_name:
                file_name = "git_report.md"
            try:
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(article)
                print(f"Article saved to {file_name}")
            except Exception as e:
                print(f"Error saving file: {e}")


if __name__ == "__main__":
    main()
