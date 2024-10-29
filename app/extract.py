import os

def extract_files_content_markdown(directory, output_file):
    """
    Recursively walks through a directory and extracts the content of each file,
    outputting it in Markdown structure.
    
    :param directory: Root directory to start the recursive search.
    :param output_file: File path where to write the extracted contents.
    """
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, _, files in os.walk(directory):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                
                # Exclude the output file itself if it's in the same directory
                if file_path == output_file:
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                    
                    # Write the file path as a markdown header (### for third level)
                    outfile.write(f"### `{file_path}`\n\n")
                    
                    # Write the content as a markdown code block
                    outfile.write("```\n")
                    outfile.write(f"{content}\n")
                    outfile.write("```\n\n")
                
                except Exception as e:
                    # Handle errors with a note in the output file
                    outfile.write(f"### `{file_path}`\n\n")
                    outfile.write("```\n")
                    outfile.write(f"Error reading file: {str(e)}\n")
                    outfile.write("```\n\n")

if __name__ == "__main__":
    # Define the directory to start from and the output file path
    root_directory = os.path.dirname(os.path.abspath(__file__))  # Current directory
    output_file = os.path.join(root_directory, 'output_markdown.txt')
    
    # Call the function to extract content
    extract_files_content_markdown(root_directory, output_file)
