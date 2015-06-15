Python3 Name Parser
-------

Features
********
- Built-in Dictionary of 150,000+ names and their popularity rankings.
- Distinguishes between last and first names.
- Last and First name sequence detection: Can detect invalid combinations of Last-First-Last name sequences and select the best option.
- Search by Popularity: best for mangled strings.
- Search by Longest Names: best for email addresses, or generally valid data.
- Uses Regex to extract letter sequences, breaking the input into words and considerably increasing matching probability.
- Worst case runtime of O(n**2) not counting the single regex operation above (where n = number of chars).
- Actual scan time is under a second, even for strings with hundreds of characters.

Usage
********
Simply call NameParser.Scan(). Input can be a string or a list of strings.

