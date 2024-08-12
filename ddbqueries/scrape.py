# Function to extract characters between column 103 and 119
def extract_columns_from_file(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            # Extract the substring from column 103 to 119 (indexes 102 to 118 in 0-based index)
            extracted_text = line[102:119]
            # Write the extracted text to the output file
            outfile.write(extracted_text + '\n')

# Example usage
input_file = 'input.txt'  # Replace with your input file path
output_file = 'output.txt'  # Replace with your desired output file path

extract_columns_from_file(input_file, output_file)