Python3 Name Parser
-------

Usage
********
Place folder in your site-packages folder, and call NameParser.Scan(<your-string-here>)

Features
********
- Worst case runtime of O :sup:'2'
- Built-in Dictionary of 150,000+ names and their popularity rankings.
- Distinguishes between last and first names.
- Last and First name sequence detection: Can detect invalid combinations of Last-First-Last name sequences and select the best option.
- Search by Popularity: best for mangled strings.
- Search by Longest Names: best for email addresses, or generally valid data.
