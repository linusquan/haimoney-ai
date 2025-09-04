# Retrive files from output/user_upload
# call extraction/gemini_file_extract.py to extract file one by one
# place the  result: str as a .md file using the original file name
# after each extraction, record the description in a <filename>-hmoney-metadata.json, error and errorReason
# if a extraction failed or with 2 minutes timeout skip and process next
# show progress of file extration in log for now
