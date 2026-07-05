import fitz


class PDFService:

    @staticmethod
    def extract_pages(
            path: str,
    ) -> list[str]:
        """
         Returns the text content of each page, in order. Used so chunks
         can be tagged with the page they came from.
        """
        document = fitz.open(path)

        try:
            return [page.get_text() for page in document]
        finally:
            document.close()


    @staticmethod
    def extract_text(
        path: str,
    ) -> str:

        return "\n".join(PDFService.extract_pages(path))