Extraction of companies  from NSE pages
1. Go to NSE page
2. Copy the html content of the table
3. Use beautiful locally to process it 

```
with open('src/sample.html', 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        
        # Find the table
        table = soup.find('table')
        
        # Open a CSV file for writing
        with open('output.csv', mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Flag to indicate whether the header has been written
            header_written = False
            
            # Iterate over each row in the table
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                
                # Skip rows that don't have any columns
                if len(cols) == 0:
                    continue
                
                # Prepare a list for the current row's data
                row_data = []
                
                for index, val in enumerate(cols):
                    # Check if there is a link in the column
                    link = val.find('a')
                    if link:
                        # Extract the href attribute if a link is found
                        row_data.append(link.get('href'))
                        row_data.append(re.sub(r'\s+', ' ', val.text).strip())
                    else:
                        # Otherwise, just append the column's text value
                        row_data.append(re.sub(r'\s+', ' ', val.text).strip())
                
                # Write header row if not written already
                if not header_written:
                    # Using the first row to create the header
                    header = ['link'] + [f'Column {i}' for i in range(len(row_data) - 1)]
                    writer.writerow(header)
                    header_written = True
                
                # Write the current row to the CSV
                writer.writerow(row_data)
```



Color Specification 
| **Color Name**    | **Description**                            | **Hex Code** | **Use Case**                                         |
|-------------------|--------------------------------------------|--------------|------------------------------------------------------|
| **Dark Gray**     | Background color (primary)                | `#1e1e1e`    | Used for the main background of the terminal interface to reduce eye strain and provide a neutral base. |
| **Light Gray**    | Secondary text color                      | `#B0B0B0`    | Used for secondary text, labels, and non-critical information to create hierarchy and contrast. |
| **White**         | Primary text color                        | `#FFFFFF`    | Used for primary text to ensure high readability and contrast against the dark background. |
| **Green**         | Positive price movement (gains)           | `#00FF00`    | Used to highlight positive financial data such as rising stock prices, gains, or increases in indices. |
| **Red**           | Negative price movement (losses)          | `#FF3B30`    | Used to indicate negative changes in financial data, like falling stock prices, market losses, or declines. |
| **Yellow/Gold**   | Highlights or alerts                      | `#F1C40F`    | Used for important alerts, warnings, or key data points that require the user's attention. |
| **Blue**          | Interactive elements (links, buttons)     | `#0072C6`    | Used for hyperlinks, buttons, and other interactive elements in the interface for user navigation. |
| **Light Blue**    | Neutral data points or graphs             | `#5DA8D6`    | Often used for neutral or non-critical data series in graphs, charts, or comparisons. |
| **Light Gray (Borders)** | Borders, dividers between sections  | `#5C5C5C`    | Used for subtle borders and dividers between sections or panels, helping to organize the layout. |


class = d-dquote-x1-5 
class = marketCap