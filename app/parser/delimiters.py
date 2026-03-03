"""Detect EDI X12 delimiters from ISA segment."""


class Delimiters:
    """Container for EDI X12 delimiters detected from the ISA segment."""

    def __init__(self, element: str, sub_element: str, segment: str):
        self.element = element
        self.sub_element = sub_element
        self.segment = segment


def detect_delimiters(raw: str) -> Delimiters:
    """Detect delimiters from ISA segment header.

    ISA is always exactly 106 characters:
    - Position 3: element separator
    - Position 104: sub-element (component) separator
    - Position 105: segment terminator
    """
    # Find ISA start
    isa_pos = raw.find("ISA")
    if isa_pos == -1:
        raise ValueError("No ISA segment found — not a valid EDI X12 file")

    header = raw[isa_pos:]
    if len(header) < 106:
        raise ValueError("ISA segment too short — file may be truncated")

    element_sep = header[3]
    sub_element_sep = header[104]
    segment_sep = header[105]

    # Handle newline as part of segment terminator
    # Some files use ~\n or ~\r\n
    return Delimiters(
        element=element_sep,
        sub_element=sub_element_sep,
        segment=segment_sep,
    )
