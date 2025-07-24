import dspy

lm = dspy.LM("openai/gpt-4o-mini", temperature=0.3, max_tokens=5000)
dspy.configure(lm=lm)


class CorrectHeadingLevelSignature(dspy.Signature):
    """Correct heading levels. Main title should be H1, Chapter Titles H2, etc."""

    headings: str = dspy.InputField(
        description=r"String of headings extracted via OCR process, separated by \n"
    )
    corrected_headings: str = dspy.OutputField(
        description="Headings with corrected level"
    )


class CorrectHeadingLevel(dspy.Module):
    def __init__(self):
        self.predictor = dspy.ChainOfThought(CorrectHeadingLevelSignature)

    def forward(self, headings):
        prediction = self.predictor(headings=headings)
        return prediction
