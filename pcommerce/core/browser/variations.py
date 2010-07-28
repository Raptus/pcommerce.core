from plone.app.content.browser.foldercontents import FolderContentsView, FolderContentsTable

from pcommerce.core.interfaces import IVariation

class Variations(FolderContentsView):
    """management view of all variations
    """
    
    def contents_table(self):
        table = FolderContentsTable(self.context, self.request, {'object_provides': IVariation.__identifier__})
        return table.render()