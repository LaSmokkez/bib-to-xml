def __read_bib_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            bib_data = file.read()

            # Remove newline characters
            bib_data = bib_data.replace('\n', '')

        return bib_data
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def __find_and_extract_entries(text):
    patterns =['@article', '@book', '@conference', '@booklet', '@incollection', '@inbook', '@inproceedings', '@manual', '@phdthesis', '@masterthesis', '@misc', '@proceedings', '@unpublished', '@techreport']
    extracted_strings = []
    all_indexes = []
    
    for pattern in patterns:
        start_index = 0
        while start_index != -1:
            start_index = text.find(pattern, start_index)
            if start_index != -1:
                all_indexes.append(start_index)
                start_index += 1
    all_indexes.append(len(text))
    unique_indexes = list(set(all_indexes))
    unique_indexes.sort()
    for i in range(len(unique_indexes) - 1):
        extracted_strings.append(text[unique_indexes[i]:unique_indexes[i+1]])            
    return extracted_strings

def __turn_bib_into_dict(list_of_bib_entries):
    # Extract the part between '@' and the first {
    entry_type_variable = list_of_bib_entries[list_of_bib_entries.find('@') + 1: list_of_bib_entries.find('{')]

    # Remove '@' and the text until the first '{'
    remaining_string = list_of_bib_entries[list_of_bib_entries.find('{'):]

    # Find the position of the last closing curly brace }
    last_brace_index = remaining_string.rfind('}')

    # Construct the modified string
    modified_bib_string = (
        list_of_bib_entries[:list_of_bib_entries.find('@')] +
        remaining_string[:last_brace_index] +
        ", ENTRYTYPE={" + entry_type_variable + "}" +
        remaining_string[last_brace_index:]
    )

    # Extract the part between "{" and the first ","
    start_index = modified_bib_string.find('{') + 1
    end_index = modified_bib_string.find(',')
    extracted_part = modified_bib_string[start_index:end_index]

    # Remove the extracted part and the first comma from the modified string
    modified_bib_string = (
        modified_bib_string[:start_index] +
        modified_bib_string[end_index+1:]
    )

    # Find the position of the last closing curly brace }
    last_brace_index = modified_bib_string.rfind('}')

    # Construct the modified string with the 'ID' key
    modified_bib_string = (
        modified_bib_string[:last_brace_index] +
        ", ID={" + extracted_part + "}" +
        modified_bib_string[last_brace_index:]
    )

    # Remove the surrounding curly braces
    content = modified_bib_string[1:-1]

    # Split the content by commas
    key_value_pairs = [pair.strip() for pair in content.split(',')]

    # Construct the reformatted string
    reformatted_string = ', '.join([
        f"'{pair.split('=')[0].strip()}': '{pair.split('=')[1].strip()}'"
        if '=' in pair else f"'{pair.strip()}'"
        for pair in key_value_pairs
    ])
    reformatted_string = modified_bib_string.replace('{', '').replace('}', '')

    space_indices = []

    # Iterate through the string from right to left
    for i in range(len(reformatted_string) - 1, -1, -1):
        if reformatted_string[i] == '=':
            # Find the index of the first space to the left of the '=' character
            space_index = reformatted_string.rfind(' ', 0, i)
            if space_index != -1:
                space_indices.append(space_index)

    # Insert '&%&' at each identified space index
    for index in space_indices:
        reformatted_string = reformatted_string[:index] + '&%&' + reformatted_string[index:]

    split_pieces = reformatted_string.split('&%&')

    # Remove leading and trailing whitespaces from each piece
    split_pieces = [piece.strip() for piece in split_pieces]
    new_string = []

    for x in split_pieces:
        last_comma_index = x.rfind(',')
        if last_comma_index != -1:
            x = x[:last_comma_index] + x[last_comma_index + 1:]
        new_string.append(x)

    filtered_entries = [entry for entry in new_string if entry != '']
    # print(filtered_entries)
    result_dict = {}

    for entry in filtered_entries:
        key, value = entry.split('=')
        result_dict[key] = value
        
    entrytype_mapping = {
        'article': 'JournalArticle',
        'book': 'Book',
        # Add more mappings as needed
    }

    if 'ENTRYTYPE' in result_dict:
        entrytype_value = result_dict['ENTRYTYPE'].lower()  # Convert to lowercase for case-insensitivity

        # Use the entrytype_mapping dictionary to replace the value
        result_dict['ENTRYTYPE'] = entrytype_mapping.get(entrytype_value, result_dict['ENTRYTYPE'])

    return result_dict

def __create_xml_entry(entry, ref_order):
    source = (
        f'<b:Source>'
    )
    
    if 'ID' in entry:      
        source += f"<b:Tag>{entry['ID']}</b:Tag>"
    
    source += f"<b:SourceType>JournalArticle</b:SourceType>"
    
    if 'title' in entry:   
        source += f"<b:Title>{entry['title']}</b:Title>"
    
    if 'year' in entry:   
        source +=f"<b:Year>{entry['year']}</b:Year>"
        
    source += (
        f"<b:Author>" 
        f"<b:Author>" 
        f"<b:NameList>"
    )

    # Splitting the author names and creating Person elements
    authors = entry['author'].split(' and ')
    for author_name in authors:
        last, first = map(str.strip, author_name.split(','))
        source += (
            f"<b:Person>"
            f"<b:Last>{last}</b:Last>"
            f"<b:First>{first}</b:First>"
            f"</b:Person>"
        )

    source += (
        f"</b:NameList>"
        f"</b:Author>"
        f"</b:Author>"
    )

    if 'journal' in entry:     
        source +=f"<b:JournalName>{entry['journal']}</b:JournalName>"
        
    if 'pages' in entry: 
        source +=f"<b:Pages>{entry['pages']}</b:Pages>"
    
    if 'place' in entry:
        city, province = map(str.strip, entry['place'].split(', '))
        source += (
            f"<b:City>{city}</b:City>"
            f"<b:StateProvince>{province}</b:StateProvince>"
        )
    
    if 'publisher' in entry:
        source +=f"<b:Publisher>{entry['publisher']}</b:Publisher>"
        
    source +=f"<b:LCID>2057</b:LCID>"
    
    if 'volume' in entry: 
        source +=f"<b:Volume>{entry['volume']}</b:Volume>"
        
    if 'number' in entry: 
        source +=f"<b:Issue>{entry['number']}</b:Issue>"
        
    if 'doi' in entry: 
        source +=f"<b:DOI>{entry['doi']}</b:DOI>"
            
    source += (
        f"<b:RefOrder>{ref_order}</b:RefOrder>"
        f"</b:Source>"
    )
        
    return source   

def bib_to_xml(file_path, output_file_path):
    bib_text = __read_bib_file(file_path)

    result = __find_and_extract_entries(bib_text)
    entries_dict = []
    for x in result:
        entries_dict.append(__turn_bib_into_dict(x))
        
    xml_entries = []
    for idx, entry in enumerate(entries_dict, start=1):
        xml_entry = __create_xml_entry(entry, ref_order=idx)
        xml_entries.append(xml_entry)

    # Combine all entries into a single XML document
    xml_document = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<b:Sources xmlns:b="http://schemas.openxmlformats.org/officeDocument/2006/bibliography" xmlns="http://schemas.openxmlformats.org/officeDocument/2006/bibliography" SelectedStyle="">\n'
        + ''.join(xml_entries)
        + '</b:Sources>'
    )

    xml_document_modified = xml_document.replace("</b:Source>", "</b:Source>\n")

    with open(output_file_path, 'w', encoding="utf-8") as file:
        file.write(xml_document_modified)