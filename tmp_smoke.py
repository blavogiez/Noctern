from llm.proofreading_apply import apply_corrections_to_text

class E:
    def __init__(self, original, suggestion, approved=True):
        self.original = original
        self.suggestion = suggestion
        self.is_approved = approved
        self.is_applied = False

text = "Hello wrld!\nThis is a sample.\nRemove this line.\n"
errs = [E('wrld','world'), E('Remove this line.','')]
res = apply_corrections_to_text(text, errs)
open('tmp_smoke_out.txt','w',encoding='utf-8').write(res)
print('OK', len(res))
