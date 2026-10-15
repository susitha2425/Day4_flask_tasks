const taskForm = document.querySelector("#task-form");

if (taskForm) {
    const taskList = document.querySelector("#task-list");
    const taskCount = document.querySelector("#task-count");
    const taskMessage = document.querySelector("#task-message");
    const titleInput = document.querySelector("#task-title");
    const submitButton = taskForm.querySelector("button[type='submit']");
    const priorities = ["Low", "Medium", "High"];

    const createTaskItem = (task) => {
        const item = document.createElement("article");
        item.className = `task-item${task.status === "Completed" ? " is-completed" : ""}`;
        item.dataset.taskId = task.id;
        item.dataset.title = task.title;
        item.dataset.status = task.status;
        item.dataset.priority = task.priority;

        const checkButton = document.createElement("button");
        checkButton.className = `task-check-button${task.status === "Completed" ? " is-completed" : ""}`;
        checkButton.type = "button";
        const isCompleted = task.status === "Completed";
        checkButton.setAttribute(
            "aria-label",
            isCompleted ? "Mark task as pending" : "Mark task as completed",
        );
        checkButton.setAttribute("aria-pressed", String(isCompleted));
        const icon = document.createElement("i");
        icon.className = isCompleted ? "bi bi-check-circle-fill" : "bi bi-circle";
        checkButton.append(icon);

        const title = document.createElement("span");
        title.className = "task-title";
        title.textContent = task.title;

        const status = document.createElement("span");
        status.className = `badge rounded-pill status-badge${isCompleted ? " completed" : ""}`;
        status.textContent = task.status;

        const priority = document.createElement("span");
        priority.className = `badge rounded-pill priority-badge priority-${task.priority.toLowerCase()}`;
        priority.textContent = task.priority;

        const actions = document.createElement("div");
        actions.className = "task-actions";
        const editButton = document.createElement("button");
        editButton.className = "btn btn-light btn-sm edit-task-button";
        editButton.type = "button";
        editButton.setAttribute("aria-label", "Edit task");
        editButton.title = "Edit task";
        editButton.innerHTML = '<i class="bi bi-pencil"></i>';
        const deleteButton = document.createElement("button");
        deleteButton.className = "btn btn-light btn-sm delete-task-button";
        deleteButton.type = "button";
        deleteButton.setAttribute("aria-label", "Delete task");
        deleteButton.title = "Delete task";
        deleteButton.innerHTML = '<i class="bi bi-trash3"></i>';
        actions.append(editButton, deleteButton);

        item.append(checkButton, title, status, priority, actions);
        return item;
    };

    const showMessage = (message) => {
        taskMessage.textContent = message;
        taskMessage.className = "alert alert-danger";
    };

    const sendTaskRequest = async (url, options) => {
        const response = await fetch(url, {
            ...options,
            headers: { Accept: "application/json", ...options.headers },
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || "Unable to update this task.");
        }
        return result;
    };

    const beginEditing = (item) => {
        if (item.querySelector(".task-edit-form")) {
            return;
        }

        const form = document.createElement("form");
        form.className = "task-edit-form";
        const title = document.createElement("input");
        title.className = "form-control";
        title.name = "title";
        title.maxLength = 250;
        title.required = true;
        title.value = item.dataset.title;

        const priority = document.createElement("select");
        priority.className = "form-select";
        priority.name = "priority";
        for (const value of priorities) {
            const option = document.createElement("option");
            option.value = value;
            option.textContent = value;
            option.selected = value === item.dataset.priority;
            priority.append(option);
        }

        const saveButton = document.createElement("button");
        saveButton.className = "btn btn-success btn-sm";
        saveButton.type = "submit";
        saveButton.textContent = "Save";
        const cancelButton = document.createElement("button");
        cancelButton.className = "btn btn-outline-secondary btn-sm cancel-edit-button";
        cancelButton.type = "button";
        cancelButton.textContent = "Cancel";

        form.append(title, priority, saveButton, cancelButton);
        item.replaceChildren(form);
        title.focus();
        title.select();
    };

    taskList.addEventListener("click", async (event) => {
        const button = event.target.closest(
            ".task-check-button, .edit-task-button, .delete-task-button, .cancel-edit-button",
        );
        if (!button) {
            return;
        }

        const item = button.closest(".task-item");
        if (button.matches(".edit-task-button")) {
            beginEditing(item);
            return;
        }
        if (button.matches(".cancel-edit-button")) {
            item.replaceWith(createTaskItem({
                id: item.dataset.taskId,
                title: item.dataset.title,
                status: item.dataset.status,
                priority: item.dataset.priority,
            }));
            return;
        }

        if (button.matches(".delete-task-button")) {
            if (!window.confirm("Delete this task? This cannot be undone.")) {
                return;
            }
            button.disabled = true;
            taskMessage.classList.add("d-none");
            try {
                await sendTaskRequest(`/delete_task/${item.dataset.taskId}`, {
                    method: "POST",
                });
                item.remove();
                taskCount.textContent = String(Number(taskCount.textContent) - 1);
                if (!taskList.querySelector(".task-item")) {
                    const empty = document.createElement("div");
                    empty.id = "empty-state";
                    empty.className = "empty-state";
                    empty.innerHTML = '<div class="empty-icon"><i class="bi bi-inbox"></i></div><h2 class="h5 fw-semibold">Your list is clear</h2><p class="text-secondary mb-0">Add your first task above and make today count.</p>';
                    taskList.append(empty);
                }
            } catch (error) {
                showMessage(error.message);
                button.disabled = false;
            }
            return;
        }

        if (!button.matches(".task-check-button")) {
            return;
        }
        button.disabled = true;
        taskMessage.classList.add("d-none");

        try {
            const result = await sendTaskRequest(`/toggle_task/${item.dataset.taskId}`, {
                method: "POST",
            });

            const isCompleted = result.status === "Completed";
            item.dataset.status = result.status;
            item.classList.toggle("is-completed", isCompleted);
            button.classList.toggle("is-completed", isCompleted);
            button.setAttribute("aria-pressed", String(isCompleted));
            button.setAttribute(
                "aria-label",
                isCompleted ? "Mark task as pending" : "Mark task as completed",
            );
            button.querySelector("i").className = isCompleted
                ? "bi bi-check-circle-fill"
                : "bi bi-circle";
            const status = item.querySelector(".status-badge");
            status.textContent = result.status;
            status.classList.toggle("completed", isCompleted);
        } catch (error) {
            showMessage(error.message);
        } finally {
            button.disabled = false;
        }
    });

    taskList.addEventListener("submit", async (event) => {
        const form = event.target.closest(".task-edit-form");
        if (!form) {
            return;
        }
        event.preventDefault();
        taskMessage.classList.add("d-none");
        const item = form.closest(".task-item");
        const saveButton = form.querySelector("button[type='submit']");
        saveButton.disabled = true;

        try {
            const result = await sendTaskRequest(`/edit_task/${item.dataset.taskId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title: form.elements.title.value.trim(),
                    priority: form.elements.priority.value,
                }),
            });
            item.replaceWith(createTaskItem(result));
        } catch (error) {
            showMessage(error.message);
            saveButton.disabled = false;
        }
    });

    taskForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        taskMessage.classList.add("d-none");
        submitButton.disabled = true;

        try {
            const result = await sendTaskRequest("/add_task", {
                method: "POST",
                body: new FormData(taskForm),
            });

            document.querySelector("#empty-state")?.remove();

            taskList.prepend(createTaskItem(result));
            taskCount.textContent = String(Number(taskCount.textContent) + 1);
            taskForm.reset();
            titleInput.focus();
        } catch (error) {
            showMessage(error.message);
        } finally {
            submitButton.disabled = false;
        }
    });
}
