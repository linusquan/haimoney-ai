#!/usr/bin/env python3
import os

def count_files_in_folders(root_path):
    """
    Count files in each child folder, excluding hidden files.
    
    Args:
        root_path (str): Path to the root directory
    
    Returns:
        dict: Dictionary with folder names as keys and file counts as values
    """
    if not os.path.exists(root_path):
        print(f"Error: Directory '{root_path}' does not exist.")
        return {}
    
    folder_counts = {}
    
    try:
        # Get all items in the root directory
        items = os.listdir(root_path)
        
        for item in items:
            item_path = os.path.join(root_path, item)
            
            # Skip hidden files/folders (starting with .)
            if item.startswith('.'):
                continue
                
            # Only process directories
            if os.path.isdir(item_path):
                file_count = 0
                
                try:
                    # Count files recursively in this directory (excluding hidden files)
                    for root, dirs, files in os.walk(item_path):
                        # Remove hidden directories from the search
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        
                        # Count non-hidden files
                        for file_item in files:
                            if not file_item.startswith('.'):
                                file_count += 1
                    
                    folder_counts[item] = file_count
                    
                except PermissionError:
                    print(f"Permission denied accessing: {item_path}")
                    folder_counts[item] = "Permission Denied"
                except Exception as e:
                    print(f"Error accessing {item_path}: {e}")
                    folder_counts[item] = "Error"
    
    except Exception as e:
        print(f"Error reading directory '{root_path}': {e}")
        return {}
    
    return folder_counts

def main():
    # Path to the Application Documents directory
    app_docs_path = "/Users/liquan/code/haimoney-ai/Applicaiton Documents"
    
    print(f"Counting files in child folders of: {app_docs_path}")
    print("=" * 60)
    
    folder_counts = count_files_in_folders(app_docs_path)
    
    if folder_counts:
        # Sort folders by name for consistent output
        for folder_name in sorted(folder_counts.keys()):
            count = folder_counts[folder_name]
            print(f"{folder_name:<30} : {count} files")
        
        print("=" * 60)
        total_folders = len(folder_counts)
        total_files = sum(count for count in folder_counts.values() if isinstance(count, int))
        print(f"Total folders: {total_folders}")
        print(f"Total files: {total_files}")
    else:
        print("No folders found or unable to access the directory.")

if __name__ == "__main__":
    main()