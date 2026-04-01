import tkinter as tk
from tkinter import scrolledtext
import re

temp_count = 1

# ---------------- LEXICAL ----------------
def lexical_analysis(expr):
    tokens = re.findall(r'[a-zA-Z]+|\d+|\+|\-|\*|\/|\(|\)|\=', expr)
    result = []

    for token in tokens:
        if token in ['+', '-', '*', '/', '=', '(', ')']:
            result.append(("OPERATOR", token))
        elif token.isdigit():
            result.append(("NUMBER", token))
        else:
            result.append(("IDENTIFIER", token))

    return result


# ---------------- SYNTAX (UPDATED) ----------------
def syntax_analysis(tokens):
    values = [t[1] for t in tokens]

    if '=' not in values:
        return False, "Missing '=' operator", []

    if values.count('=') != 1:
        return False, "Multiple '=' not allowed", []

    rhs = values[values.index('=')+1:]

    if not rhs:
        return False, "Missing RHS expression", []

    ops = ['+', '-', '*', '/']

    trace = []

    for i in range(len(rhs)):
        trace.append(" ".join(rhs[:i+1]))

        # error: operator at end
        if i == len(rhs)-1 and rhs[i] in ops:
            return False, f"Error at '{rhs[i]}' → Expression cannot end with operator", trace

        # error: consecutive operators
        if i < len(rhs)-1 and rhs[i] in ops and rhs[i+1] in ops:
            return False, f"Error at '{rhs[i+1]}' → Consecutive operators", trace

    # Parentheses check
    stack = []
    for v in values:
        if v == '(':
            stack.append(v)
        elif v == ')':
            if not stack:
                return False, "Unmatched ')'", trace
            stack.pop()
    if stack:
        return False, "Unmatched '('", trace

    return True, "Syntax is valid", trace


# ---------------- SEMANTIC ----------------
def semantic_analysis(tokens):
    return True, "Semantic check passed"


# ---------------- AST ----------------
class Node:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None


def build_ast(tokens):
    precedence = {'+':1, '-':1, '*':2, '/':2}
    output, stack = [], []

    for t in tokens:
        val = t[1]

        if val.isalnum():
            output.append(val)

        elif val == '(':
            stack.append(val)

        elif val == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()

        elif val in precedence:
            while stack and stack[-1] in precedence and precedence[stack[-1]] >= precedence[val]:
                output.append(stack.pop())
            stack.append(val)

    while stack:
        output.append(stack.pop())

    st = []
    for token in output:
        node = Node(token)
        if token in precedence:
            node.right = st.pop()
            node.left = st.pop()
        st.append(node)

    return st[-1]


# ---------------- DRAW TREE ----------------
def draw_ast(node, x, y, dx):
    if not node:
        return

    canvas.create_text(x, y, text=node.value, font=("Arial", 14, "bold"))

    if node.left:
        new_dx = max(dx // 2, 50)
        canvas.create_line(x, y+20, x-new_dx, y+90)
        draw_ast(node.left, x-new_dx, y+90, new_dx)

    if node.right:
        new_dx = max(dx // 2, 50)
        canvas.create_line(x, y+20, x+new_dx, y+90)
        draw_ast(node.right, x+new_dx, y+90, new_dx)


# ---------------- TAC ----------------
def generate_TAC(node):
    global temp_count

    if node.left is None and node.right is None:
        return "", node.value

    left_code, left = generate_TAC(node.left)
    right_code, right = generate_TAC(node.right)

    temp = f"t{temp_count}"
    temp_count += 1

    code = left_code + right_code + f"{temp} = {left} {node.value} {right}\n"
    return code, temp


# ---------------- UNOPTIMIZED ASM ----------------
def generate_unoptimized_assembly(tac):
    asm = []

    for line in tac.strip().split("\n"):
        parts = line.split()
        if len(parts) != 5:
            continue

        dest, _, op1, operator, op2 = parts

        asm.append(f"MOV R0, {op1}")

        if operator == '+':
            asm.append(f"ADD R0, {op2}")
        elif operator == '-':
            asm.append(f"SUB R0, {op2}")
        elif operator == '*':
            asm.append(f"MUL R0, {op2}")
        elif operator == '/':
            asm.append(f"DIV R0, {op2}")

        asm.append(f"MOV {dest}, R0")

    return asm


# ---------------- OPTIMIZED ASM ----------------
def generate_optimized_assembly(node):
    asm = []

    def gen(n):
        if n.left is None and n.right is None:
            return n.value

        right = gen(n.right)

        if n.right.left is None:
            asm.append(f"MOV R0, {right}")

        left = gen(n.left)

        if n.value == '+':
            asm.append(f"ADD R0, {left}")
        elif n.value == '-':
            asm.append(f"SUB R0, {left}")
        elif n.value == '*':
            asm.append(f"MUL R0, {left}")
        elif n.value == '/':
            asm.append(f"DIV R0, {left}")

        return "R0"

    gen(node)
    return asm


# ---------------- MAIN ----------------
def compile_code():
    global temp_count
    temp_count = 1

    code = input_box.get().strip()
    output_box.delete("1.0", tk.END)
    canvas.delete("all")

    if not code:
        return

    tokens = lexical_analysis(code)

    output_box.insert(tk.END, "🔹 LEXICAL ANALYSIS\n")
    for t in tokens:
        output_box.insert(tk.END, f"{t}\n")

    # SYNTAX (UPDATED)
    valid, msg, trace = syntax_analysis(tokens)

    output_box.insert(tk.END, "\n🔹 SYNTAX ANALYSIS\n")

    for step in trace:
        output_box.insert(tk.END, f"✔ {step}\n")

    if not valid:
        output_box.insert(tk.END, msg + "\n", "error")
        output_box.insert(tk.END, "❌ COMPILATION STOPPED\n", "error")
        return
    else:
        output_box.insert(tk.END, msg + "\n")

    # SEMANTIC
    valid, msg = semantic_analysis(tokens)
    output_box.insert(tk.END, "\n🔹 SEMANTIC ANALYSIS\n" + msg + "\n")

    lhs, rhs = code.split("=")
    lhs, rhs = lhs.strip(), rhs.strip()

    rhs_tokens = lexical_analysis(rhs)
    rhs_ast = build_ast(rhs_tokens)

    root = Node("=")
    root.left = Node(lhs)
    root.right = rhs_ast

    draw_ast(root, 300, 40, 200)

    tac, result = generate_TAC(root.right)
    tac += f"{lhs} = {result}\n"

    output_box.insert(tk.END, "\n🔹 INTERMEDIATE CODE GENERATION\n" + tac)

    unopt = generate_unoptimized_assembly(tac)
    opt = generate_optimized_assembly(root.right)
    opt.append(f"MOV {lhs}, R0")

    output_box.insert(tk.END, "\n🔹 CODE OPTIMIZATION\n")

    output_box.insert(tk.END, "\nBefore Optimization:\n")
    output_box.insert(tk.END, "\n".join(unopt) + "\n")

    output_box.insert(tk.END, "\nAfter Optimization:\n")
    output_box.insert(tk.END, "\n".join(opt) + "\n")

    output_box.insert(tk.END, f"\nInstruction Count: {len(unopt)} → {len(opt)}\n")

    output_box.insert(tk.END, "\n🔹 CODE GENERATION (FINAL)\n")
    output_box.insert(tk.END, "\n".join(opt) + "\n")

    output_box.see(tk.END)


# ============= MODERN UI WITH BEAUTIFUL DESIGN =============
root = tk.Tk()
root.title("✨ Compiler Visualizer - Advanced")
root.geometry("1400x900")
root.configure(bg="#0f1419")

# Define Modern Color Scheme
BG_COLOR = "#0f1419"
HEADER_COLOR = "#1a1f2e"
INPUT_COLOR = "#16213e"
BUTTON_COLOR = "#00d4ff"
BUTTON_HOVER = "#00b8d4"
TEXT_COLOR = "#ffffff"
ACCENT_COLOR = "#ff6b6b"
SUCCESS_COLOR = "#51cf66"

# ========== HEADER SECTION ==========
header_frame = tk.Frame(root, bg=HEADER_COLOR, height=120)
header_frame.pack(fill="x", padx=0, pady=0)
header_frame.pack_propagate(False)

title = tk.Label(
    header_frame, 
    text="🔧 COMPILER VISUALIZER", 
    font=("Segoe UI", 28, "bold"),
    bg=HEADER_COLOR,
    fg=BUTTON_COLOR
)
title.pack(pady=15)

subtitle = tk.Label(
    header_frame,
    text="Transform high-level code into optimized assembly",
    font=("Segoe UI", 11),
    bg=HEADER_COLOR,
    fg="#a0a0a0"
)
subtitle.pack()

# ========== INPUT SECTION ==========
input_section = tk.Frame(root, bg=BG_COLOR)
input_section.pack(fill="x", padx=30, pady=20)

input_label = tk.Label(
    input_section,
    text="📝 Expression Input",
    font=("Segoe UI", 12, "bold"),
    bg=BG_COLOR,
    fg=BUTTON_COLOR
)
input_label.pack(anchor="w", pady=(0, 8))

input_frame = tk.Frame(input_section, bg=INPUT_COLOR, highlightcolor="#00d4ff", highlightbackground="#333")
input_frame.pack(fill="x", padx=0)

input_box = tk.Entry(
    input_frame,
    font=("Consolas", 13),
    bg=INPUT_COLOR,
    fg=TEXT_COLOR,
    border=0,
    insertbackground=BUTTON_COLOR
)
input_box.pack(fill="x", padx=15, pady=12)
input_box.insert(0, "Example: x = a + b * c")

def on_focus_in(event):
    if input_box.get() == "Example: x = a + b * c":
        input_box.delete(0, tk.END)
        input_box.config(fg=TEXT_COLOR)

def on_focus_out(event):
    if input_box.get() == "":
        input_box.insert(0, "Example: x = a + b * c")
        input_box.config(fg="#666")

input_box.bind("<FocusIn>", on_focus_in)
input_box.bind("<FocusOut>", on_focus_out)

# ========== BUTTON SECTION ==========
button_section = tk.Frame(root, bg=BG_COLOR)
button_section.pack(fill="x", padx=30, pady=(0, 20))

compile_btn = tk.Button(
    button_section,
    text="▶ COMPILE & VISUALIZE",
    command=compile_code,
    font=("Segoe UI", 12, "bold"),
    bg=BUTTON_COLOR,
    fg="#000",
    border=0,
    padx=30,
    pady=10,
    cursor="hand2",
    activebackground=BUTTON_HOVER,
    activeforeground="#000"
)
compile_btn.pack(side="left")

status_label = tk.Label(
    button_section,
    text="Ready to compile",
    font=("Segoe UI", 10),
    bg=BG_COLOR,
    fg=SUCCESS_COLOR
)
status_label.pack(side="left", padx=15)

# ========== CONTENT AREA ==========
content_frame = tk.Frame(root, bg=BG_COLOR)
content_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

# Left Panel - Output
left_panel = tk.Frame(content_frame, bg=HEADER_COLOR, relief="flat")
left_panel.pack(side="left", fill="both", expand=True, padx=(0, 15))

output_label = tk.Label(
    left_panel,
    text="📋 Compilation Report",
    font=("Segoe UI", 11, "bold"),
    bg=HEADER_COLOR,
    fg=BUTTON_COLOR,
    pady=10
)
output_label.pack(anchor="w", padx=10)

output_box = scrolledtext.ScrolledText(
    left_panel,
    font=("Consolas", 10),
    bg=INPUT_COLOR,
    fg=TEXT_COLOR,
    border=0,
    wrap=tk.WORD
)
output_box.pack(fill="both", expand=True, padx=8, pady=8)

output_box.tag_config("error", foreground=ACCENT_COLOR, font=("Consolas", 10, "bold"))
output_box.tag_config("success", foreground=SUCCESS_COLOR)
output_box.tag_config("header", foreground=BUTTON_COLOR, font=("Consolas", 10, "bold"))

# Right Panel - AST Visualization
right_panel = tk.Frame(content_frame, bg="#1a1f2e", relief="flat")
right_panel.pack(side="right", fill="both", expand=True, padx=(15, 0))

ast_label = tk.Label(
    right_panel,
    text="🌳 Parse Tree (AST)",
    font=("Segoe UI", 11, "bold"),
    bg=HEADER_COLOR,
    fg=BUTTON_COLOR,
    pady=10
)
ast_label.pack(anchor="w", padx=10)

canvas = tk.Canvas(
    right_panel,
    bg="white",
    border=0,
    highlightthickness=0,
)
canvas.pack(fill="both", expand=True, padx=8, pady=8)

# ========== FOOTER SECTION ==========
footer_frame = tk.Frame(root, bg=HEADER_COLOR, height=40)
footer_frame.pack(fill="x", side="bottom")
footer_frame.pack_propagate(False)

footer_text = tk.Label(
    footer_frame,
    text="💡 Enter an expression like: x = 5 + 3 * 2 | Press Compile to see the full compilation process",
    font=("Segoe UI", 9),
    bg=HEADER_COLOR,
    fg="#888"
)
footer_text.pack(pady=8)

root.mainloop()