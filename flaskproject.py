from flask import Flask, request, render_template, send_file
import pandas as pd
import numpy as np
import io

app = Flask(__name__)

@app.route("/")
def upload_form():
    return '''
    <!doctype html>
    <title>Upload CSV</title>
    <h1>MSUVDL Toxicology File Converter</h1>
    <form method="POST" action="/process" enctype="multipart/form-data">
        <input type="file" name="file" accept=".csv">
        <input type="submit" value="Upload">
    </form>
    '''

@app.route("/process", methods=["POST"])
def process_file():
    if "file" not in request.files:
        return "No file part"
    
    file = request.files["file"]
    if file.filename == "":
        return "No selected file"
    
    if file and file.filename.endswith(".csv"):
        try:
            # Read the uploaded file into a pandas DataFrame
            data = pd.read_csv(file)
            
            # Process the data
            rows = data['Component Name'].unique()
            columns = ['Sample'] + list(rows)
            output = pd.DataFrame(columns=columns)

            # Create the vector to hold the masses
            masses = {}
            for val in rows:
                matching_row = data[data['Component Name'] == val]
                if not matching_row.empty:
                    masses[val] = matching_row['Mass Info'].iloc[0]

            # Convert masses to a list of values
            mass_info = list(masses.values()) 
            mass_info_with_label = ['Mass Info'] + mass_info  # Prepend the label
            output.loc[0] = mass_info_with_label

            # Extract the unique values for the samples
            samples = data['Sample Name'].unique()

            for samp in samples:
                val = samp
                selected_values_vector = [val]

                for row in rows:
                    filtered_data = data[(data['Sample Name'] == samp) & (data['Component Name'] == row)]
                    if not filtered_data.empty:
                        selected_value = filtered_data['Calculated Concentration'].iloc[0]
                        selected_value = selected_value.item()
                    else:
                        selected_value = pd.NA
                        
                    selected_values_vector.append(selected_value)

                # Add new values to the dataframe 
                new_row = pd.DataFrame([selected_values_vector], columns=output.columns) 
                output = pd.concat([output, new_row], ignore_index=True) 

            # Save to a BytesIO stream instead of file
            output_csv = io.BytesIO()
            output.to_csv(output_csv, index=False)
            output_csv.seek(0)

            return send_file(
                output_csv,
                mimetype="text/csv",
                as_attachment=True,
                download_name="processed_data.csv"
            )
        except Exception as e:
            return f"Error processing file: {e}"
    else:
        return "Invalid file type. Please upload a CSV file."

if __name__ == "__main__":
    app.run(debug=True)
