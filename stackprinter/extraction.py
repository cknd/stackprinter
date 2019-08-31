import stack_data


class FrameInfo(stack_data.FrameInfo):
    def __str__(self):
        return ("<FrameInfo %s, line %s, scope %s>" %
                (self.code.co_filename, self.lineno, self.code.co_name))


def get_info(tb_or_frame):
    if isinstance(tb_or_frame, FrameInfo):
        return tb_or_frame

    return FrameInfo(tb_or_frame, stack_data.Options(include_signature=True))
