Here are **side-by-side migration examples** from the **Assistants API** (deprecated) to the **Responses API**.

---

### 1. **Basic Chat Completion**

#### Assistants API (v2)

```python
from openai import OpenAI
client = OpenAI()

# Create a thread & run
assistant = client.beta.assistants.retrieve("asst_123")
thread = client.beta.threads.create()
run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="Hello, what can you do?"
)

# Retrieve response
output = client.beta.threads.runs.retrieve(
    thread_id=thread.id,
    run_id=run.id
)
print(output)
```

#### Responses API

```python
from openai import OpenAI
client = OpenAI()

response = client.responses.create(
    model="gpt-5",
    input="Hello, what can you do?"
)

print(response.output_text)
```

**Key Change:**

* No threads or assistant objects needed.
* State is handled with `previous_response_id` if you want to continue a conversation.

---

### 2. **Maintaining Conversation Context**

#### Assistants API

```python
run1 = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="What's the capital of France?"
)

run2 = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="And what's its population?"
)
```

#### Responses API

```python
# First message
response1 = client.responses.create(
    model="gpt-5",
    input="What's the capital of France?"
)

# Continue conversation
response2 = client.responses.create(
    model="gpt-5",
    input="And what's its population?",
    previous_response_id=response1.id
)
```

**Key Change:**

* Use `previous_response_id` to maintain context between calls.

---

### 3. **Using Tools (e.g., Code Interpreter)**

#### Assistants API

```python
run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="Plot a sine wave",
    tools=[{"type": "code_interpreter"}]
)
```

#### Responses API

```python
response = client.responses.create(
    model="gpt-5",
    input="Plot a sine wave",
    tools=[{"type": "code_interpreter"}]
)
```

---

### 4. **File Search / Retrieval**

#### Assistants API

```python
file = client.files.create(file=open("data.pdf", "rb"), purpose="assistants")
assistant = client.beta.assistants.update(
    assistant.id,
    tools=[{"type": "file_search"}],
    file_ids=[file.id]
)
```

#### Responses API

```python
file = client.files.create(file=open("data.pdf", "rb"), purpose="responses")

response = client.responses.create(
    model="gpt-5",
    input="Summarize the uploaded PDF.",
    tools=[{"type": "file_search"}],
    file_ids=[file.id]
)
```

---

Would you like me to:

1. **Create a complete migration cheat sheet** (all common patterns)?
2. **Show a real-world example** (e.g., chatbot with memory + file search + code execution)?
3. **Provide JavaScript/Node.js version** as well?

Which one do you want? Or all three?
