from flask import Flask, request, render_template_string
from collections import Counter
from statistics import mean, median, stdev
from concurrent.futures import ThreadPoolExecutor
import re 
import os

app = Flask(__name__)

STOP_WORDS = set([
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she",
    "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that",
    "these", "those", "am", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "having", "do", "does", "did", "doing",
    "a", "an", "the", "and", "but", "if", "or", "because", "as", "until",
    "while", "of", "at", "by", "for", "with", "about", "against", "between",
    "into", "through", "during", "before", "after", "above", "below", "to",
    "from", "up", "down", "in", "out", "on", "off", "over", "under", "again",
    "further", "then", "once", "here", "there", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
    "very", "s", "t", "can", "will", "just", "don", "should", "now"
])

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Task_A Text Analysis App</title>
    <style>
        body { font-family: Arial; margin: 40px; background: #f4f4f4; }
        .box { background: white; padding: 25px; border-radius: 10px; }
        h1 { color: #333; }
        pre {
    background: #eee;
    padding: 15px;
    border-radius: 8px;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-wrap: break-word;
}
        button { padding: 10px 20px; margin-top: 10px; }
    </style>
</head>
<body>
<div class="box">
    <h1>Task_A Text Analysis App</h1>
    <form method="POST" enctype="multipart/form-data">
        <p>Select one or more text files:</p>
        <input type="file" name="files" multiple required>

        <p>Select analyses:</p>
        <input type="checkbox" name="analysis" value="word_frequency"
        {% if 'word_frequency' in selected_analyses %}checked{% endif %}> Word Frequency<br>
        <input type="checkbox" name="analysis" value="sentence_start"
        {% if 'sentence_start' in selected_analyses %}checked{% endif %}> Sentence Start Words<br>
        <input type="checkbox" name="analysis" value="sentence_length"
        {% if 'sentence_length' in selected_analyses %}checked{% endif %}> Sentence Length Distribution<br>
        <button type="submit">Analyse</button>
    </form>

    {% if results %}
        <h2>Results</h2>
        {% for filename, result in results.items() %}
            <h3>{{ filename }}</h3>
            <pre>{{ result }}</pre>
        {% endfor %}
    {% endif %}
</div>
</body>
</html>
"""

def clean_words(text):
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return [word for word in words if word not in STOP_WORDS]

def word_frequency_analysis(text):
    words = clean_words(text)
    return Counter(words).most_common(20)

def sentence_start_words(text):
    sentences = re.split(r"[.!?]+", text)
    start_words = []

    for sentence in sentences:
        words = re.findall(r"[a-zA-Z]+", sentence.lower())
        if words:
            start_words.append(words[0])

    return Counter(start_words).most_common(10)

def sentence_length_distribution(text):
    sentences = re.split(r"[.!?]+", text)
    lengths = []

    for sentence in sentences:
        words = re.findall(r"[a-zA-Z]+", sentence)
        if words:
            lengths.append(len(words))

    if len(lengths) == 0:
        return {"mean": 0, "median": 0, "standard_deviation": 0}

    if len(lengths) == 1:
        return {
            "mean": lengths[0],
            "median": lengths[0],
            "standard_deviation": 0
        }

    return {
        "mean": round(mean(lengths), 2),
        "median": median(lengths),
        "standard_deviation": round(stdev(lengths), 2)
    }

def analyse_file(file_data, selected_analyses):
    text = file_data.decode("utf-8", errors="ignore")
    output = {}

    if "word_frequency" in selected_analyses:
        output["Top 20 Word Frequency"] = word_frequency_analysis(text)

    if "sentence_start" in selected_analyses:
        output["Top 10 Sentence Start Words"] = sentence_start_words(text)

    if "sentence_length" in selected_analyses:
        output["Sentence Length Distribution"] = sentence_length_distribution(text)

    return output

@app.route("/", methods=["GET", "POST"])
def index():
    results = {}

    selected_analyses = [
        "word_frequency",
        "sentence_start",
        "sentence_length"
    ]

    if request.method == "POST":
        files = request.files.getlist("files")
        selected_analyses = request.form.getlist("analysis")

        with ThreadPoolExecutor() as executor:
            future_results = {
                file.filename: executor.submit(analyse_file, file.read(), selected_analyses)
                for file in files
            }

            for filename, future in future_results.items():
                results[filename] = future.result()

    return render_template_string(
        HTML,
        results=results,
        selected_analyses=selected_analyses
    )
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)