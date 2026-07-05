import fitz


class PDFService:

    @staticmethod
    def extract_text(
        path: str,
    ) -> str:

        document = fitz.open(path)

        pages = []

        for page in document:

            pages.append(
                page.get_text()
            )

        document.close()

        return "\n".join(pages)