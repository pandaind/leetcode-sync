import os
import requests
from datetime import datetime, timedelta
import pytz

# Directory to store LeetCode solutions locally
LOCAL_REPO_DIR = "./codes"

# File to read LeetCode session cookie from
COOKIE_FILE_PATH = "./cookie.txt"

# LeetCode username
LEETCODE_USERNAME = "pandaind"  # Replace with your LeetCode username

# Load LeetCode session cookie from file
def load_cookie():
    try:
        with open(COOKIE_FILE_PATH, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        raise Exception(f"Cookie file not found at {COOKIE_FILE_PATH}. Please create the file and add your LeetCode session cookie.")

# LeetCode session cookie loaded from file
LEETCODE_COOKIE = load_cookie()


# LeetCode GraphQL endpoint
GRAPHQL_URL = "https://leetcode.com/graphql"

# Function to get solutions from LeetCode using cookies
def fetch_leetcode_solutions():
    # Use session with cookies for authenticated requests
    session = requests.Session()
    session.headers.update({'Cookie': LEETCODE_COOKIE})

    # Fetch user submissions
    submissions_url = f"https://leetcode.com/api/submissions/?username={LEETCODE_USERNAME}"
    response = session.get(submissions_url)

    if response.status_code != 200:
        raise Exception("Failed to fetch submissions from LeetCode. Please check your cookies or network connection.")

    submissions = response.json()
    
    solutions = []
    today = datetime.now(pytz.utc).date()  # Get today's date in UTC
    today = today - timedelta(days=1)
    for submission in reversed(submissions.get('submissions_dump', [])):
        submission_time = datetime.fromtimestamp(submission['timestamp'], pytz.utc).date()
        
        if submission_time == today and submission.get('status_display') == 'Accepted':
            solutions.append({
                "title": submission.get('title'),
                "code": submission.get('code'),
                "language": submission.get('lang'),
                "slug": submission.get('title_slug')  # Assuming title_slug is available
            })
    return solutions

# Function to fetch problem details using GraphQL
def fetch_problem_details(slug):
    # Define the GraphQL query
    query = {
        "query": """
        query getQuestionDetail($titleSlug: String!) {
          question(titleSlug: $titleSlug) {
            title
            content
            difficulty
            exampleTestcases
          }
        }
        """,
        "variables": {"titleSlug": slug}
    }

    # Send a POST request to the GraphQL endpoint
    response = requests.post(GRAPHQL_URL, json=query, headers={'Cookie': LEETCODE_COOKIE})

    if response.status_code != 200:
        raise Exception(f"Failed to fetch problem details for {slug}. Please check your cookies or network connection.")

    data = response.json()
    
    # Extract the content
    problem_details = data['data']['question']
    
    return problem_details

# Function to save solutions locally
def save_solutions_locally(solutions):
    for solution in solutions:
        # Create a folder for each problem
        problem_folder = os.path.join(LOCAL_REPO_DIR, solution['title'].replace(' ', '_'))
        os.makedirs(problem_folder, exist_ok=True)

        # Save the code file
        code_filename = f"solution.{solution['language']}"
        code_filepath = os.path.join(problem_folder, code_filename)
        with open(code_filepath, "w") as file:
            file.write(solution['code'])

        # Fetch the problem details using the GraphQL API
        problem_details = fetch_problem_details(solution['slug'])

        # Save a README.md file with the problem's content
        readme_filepath = os.path.join(problem_folder, "README.md")
        with open(readme_filepath, "w") as readme_file:
            readme_file.write(f"# {problem_details['title']}\n\n")
            readme_file.write(f"**Difficulty**: {problem_details['difficulty']}\n\n")
            readme_file.write(problem_details['content'])

# Main function to run the sync process
def main():
    # Fetch solutions from LeetCode
    solutions = fetch_leetcode_solutions()

    # Save solutions locally
    save_solutions_locally(solutions)
    
if __name__ == "__main__":
    main()
