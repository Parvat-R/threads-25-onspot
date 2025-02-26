import re
import pprint
from collections import defaultdict
import database as db


def get_each_event_count():
    events = {}
    for event in db.events:
        # Replace count() with len(list()) or use count_documents()
        events[event] = db.students_collection.count_documents({"events": event})
    return events

def get_each_workshop_count():
    workshops = {}
    for workshop in db._workshops:
        workshops[workshop] = db.students_collection.count_documents({"workshop": workshop})
    return workshops

# def normalize_college_name(name):
#     """Normalize college name by cleaning up formatting and standardizing common terms."""
#     if not isinstance(name, str):
#         return "unknown"
    
#     # Convert to lowercase and remove leading/trailing whitespace
#     name = name.strip().lower()
    
#     # Replace multiple spaces with a single space
#     name = re.sub(r'\s+', ' ', name)
    
#     # Remove locations, autonomous status, and other common suffixes
#     name = re.sub(r'(?:,|\s)\s*(autonomous|namakkal|salem|karur|rasipuram|tiruchengode|dharmapuri|coimbatore|chennai).*$', '', name, flags=re.IGNORECASE)
    
#     # Standardize common abbreviations
#     name = re.sub(r'\bcollage\b', 'college', name)
#     name = re.sub(r'\bengeneering\b', 'engineering', name)
#     name = re.sub(r'\benigineering\b', 'engineering', name)
#     name = re.sub(r'\binstitue\b', 'institute', name)
    
#     # Remove articles and common words that might be omitted
#     name = re.sub(r'^the\s+', '', name)
    
#     # Remove trailing spaces, commas, dots
#     name = re.sub(r'[,.\s]+$', '', name)
    
#     return name

# def get_normalized_each_college_count():
#     """Get a count of students from each college with normalized college names."""
#     # First, get all distinct college names to group similar ones
#     all_colleges = db.students_collection.distinct("college_name")
    
#     # Create a mapping from original to normalized names
#     name_mapping = {}
#     for college in all_colleges:
#         normalized = normalize_college_name(college)
#         name_mapping[college] = normalized
    
#     # Now create clusters of similar names
#     clusters = defaultdict(list)
#     for original, normalized in name_mapping.items():
#         clusters[normalized].append(original)
    
#     # Get counts for each cluster
#     normalized_counts = {}
#     for normalized, originals in clusters.items():
#         total_count = 0
#         for original in originals:
#             count = db.students_collection.count_documents({"college_name": original})
#             total_count += count
#         normalized_counts[normalized] = total_count
    
#     # Sort by count in descending order
#     return dict(sorted(normalized_counts.items(), key=lambda x: x[1], reverse=True))

# def get_college_name_mapping():
#     """Return a mapping showing which original names map to which normalized names."""
#     all_colleges = db.students_collection.distinct("college_name")
    
#     clusters = defaultdict(list)
#     for college in all_colleges:
#         normalized = normalize_college_name(college)
#         clusters[normalized].append(college)
    
#     return dict(clusters)


if __name__ == "__main__":
    print("Each Event Count:")
    pprint.pprint(get_each_event_count())
    print("Each Workshop Count:")
    pprint.pprint(get_each_workshop_count())
