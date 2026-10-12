'''
"*Annotation" classes contain a single pure method, "annotate()", 
that maps the contents of a table (represented as a list of lists of strings)
to lists of annotation tuples where 'cell' is the contents of a cell within the table,
 and 'annotations' is a dict of attribute:keyword associated with a cell.

The concept of an "*Annotation" class is useful since we see 
there are many ways information can be stored in tables 
and each way requires its own type of supporting information regarding the nature of the table
'''

class RowAnnotation:
    '''
    `RowAnnotation` instances represent a typical system for storing tabular data
    in which each column is associated with an attribute 
    and any cell within that column is automatically assumed to be a value for the associated attribute.
    '''
    def __init__(self, header_column_names):
        self.header_column_names = header_column_names
    def annotate(self, rows):
        annotations = []
        for row in rows:
            dict_row = {key:value 
                for (key,value) in zip(self.header_column_names, row)
                if value}
            annotations.append(dict_row)
        return annotations

class CellAnnotation:
    '''
    `CellAnnotation` instances represent a system for storing tabular data 
    that comes up naturally in things like conjugation or declension tables.

    A table has a certain number of header rows and header columns.
    To avoid the user having to specify these numbers with each call to `annotate()`,
     any cell that belongs to both a header row and header column (i.e. in the "top left corner" or "canton")
     will by convention contain a constant value indicated by `canton_value`.
    When a predifined keyword occurs within the cell contents of a header row or column, 
     the row or column associated with that header is marked as having that keyword 
     for an associated attribute.
    Keywords are indicated by keys within `term_to_termaxis`.
    Keywords that are not known at the time of execution may be 
     indicated using `header_column_id_to_termaxis`, 
     which marks all cell contents of a given column as keywords for a given attribute.

    As an example, if a header row is marked 'green', and 'green' is a type of 'color',
     then `term_to_termaxis` may store 'green':'color' as a key:value pair.
    Anytime 'green' is listed in a header row or column, 
     all contents of the row or column associated with that header cell 
     will be marked as having the color 'green'.

    `CellAnnotation` converts tables that are written in this manner between 
    two reprepresentations: 
    The first representation is a list of rows, where rows are lists of cell contents.
    The second representation is a list where each element is annotation,
     i.e., a dict of attribute:keyword where cell contents are associated with a given attribute, `cell_termaxis`.
    '''
    def __init__(self, cell_termaxis, term_to_termaxis, 
            header_row_id_to_termaxis, header_column_id_to_termaxis,
            default_attributes, canton_value='*', debug=False):
        self.cell_termaxis = cell_termaxis
        self.term_to_termaxis = term_to_termaxis
        self.header_column_id_to_termaxis = header_column_id_to_termaxis
        self.header_row_id_to_termaxis = header_row_id_to_termaxis
        self.default_attributes = default_attributes
        self.canton_value = canton_value
        self.debug = debug
    def annotate(self, rows):
        header_row_count = float('inf')
        header_column_count = 0
        column_count = max([len(row) for row in rows])
        column_based_attributes = [{} for i in range(column_count)]
        annotations = []
        for i, row in enumerate(rows):
            if i < header_row_count and row[0] == self.canton_value: # header row identified
                for j, cell in enumerate(row):
                    if cell == self.canton_value:
                        header_column_count = max(header_column_count, j+1)
                    if i in self.header_row_id_to_termaxis:
                        column_based_attributes[j][self.header_row_id_to_termaxis[i]] = cell
                    elif cell in self.term_to_termaxis:
                        column_based_attributes[j][self.term_to_termaxis[cell]] = cell
                    elif cell and cell!=self.canton_value:
                        raise ValueError(f'The cell at row {i}, column {j} contains an invalid term: "{cell}"')
            else:
                header_row_count = min(header_row_count, i)
                row_based_attributes = {}
                if len(row) >= header_column_count:
                    for i in range(header_column_count):
                        cell = row[i]
                        if i in self.header_column_id_to_termaxis:
                            row_based_attributes[self.header_column_id_to_termaxis[i]] = cell
                        elif cell in self.term_to_termaxis:
                            row_based_attributes[self.term_to_termaxis[cell]] = cell
                    for i in range(header_column_count,len(row)):
                        cell = row[i]
                        if cell and (row_based_attributes or column_based_attributes[i]):
                            annotation = {
                                **self.default_attributes,
                                **row_based_attributes,
                                **column_based_attributes[i],
                                self.cell_termaxis: cell
                            }
                            annotations.append(annotation)
        return annotations
