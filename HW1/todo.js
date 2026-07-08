"use strict"; // enables strict mode and enforces stricter parsing
function normalValidateForm() {
    const task = document.getElementById("task").value.trim();
    const priority = document.getElementById("priority").value;

    if (!task || !priority) {
        alert("Both fields are required!");
        return false;
    }
    console.log("Form validation successful.")
    return true;
}

// Arrow function to validate form inputs
const validateForm = () => {
    const task = document.getElementById("task").value.trim();
    const priority = document.getElementById("priority").value;

    if (!task || !priority) {
        alert("Both fields are required!");
        return false;
    }
    return true;
};

// Closure to track the total number of tasks. Closure allows function to access variables from its outer (enclosing) function.
// it has access to variables from its outer function
const taskCounter = (() => {
    let count = 0;
    return () => ++count;
})();

// Simulate an asynchronous operation (e.g., saving task to a server)
const saveTaskToServer = (taskData) => {
    /// A Promise in JavaScript is an object that represents the eventual completion (or failure) of an asynchronous operation///
    return new Promise((resolve, reject) => {
        console.log("Saving task to server...");
        setTimeout(() => {
            // Simulate success or failure randomly
            const success = Math.random() > 0.2; // 80% success rate
            if (success) {
                resolve(`Task "${taskData.task}" saved successfully!`);
            } else {
                reject("Failed to save the task. Please try again.");
            }
        }, 2000); // Simulate a 2-second delay
    });
};

// Add an event listener to the form
// Event is basically an action or occurence in the browser.
// callback function can be thought of as function that is executed when an event is triggered.
document.getElementById("todoForm").addEventListener("submit", async (e) => {
    e.preventDefault(); //// Prevents the form from actually submitting (default behavior) and reloading the page
    
    // Validate form
    // console.log(normalValidateForm()); // normal function
     if (!validateForm()) return; // arrow function

/* 
    // Normal Function Vs Arrow Function
    const formValidator = {
        task: "Task 1",
        priority: "High",
        
        // Regular function
        regularValidateForm: function() {
            console.log("Inside regular function, this refers to:", this);
        },
        
        // Arrow function
        arrowValidateForm: () => {
            console.log("Inside arrow function, this refers to:", this);
        }
    };
    
    // Call the methods
    console.log("Calling regular function:");
    formValidator.regularValidateForm();  // `this` refers to the object
    
    console.log("Calling arrow function:");
    formValidator.arrowValidateForm();  // `this` refers to global object/window or undefined
*/

    
/* 
    // call, apply and bind
    const toDo = {
        task: "Task 3",
        priority: "Medium",
        showTask: function (msg) {
            console.log(msg + this.priority + ": " + this.task);
        }
    }
    // calling the method normally
    // toDo.showTask();

    // call method
    // call() lets you immediately invoke the function with a specified this value, and pass arguments as a list.
    const anotherTask = {task: "Task 5", priority: "High"}
    toDo.showTask.call(anotherTask, "Task details: ") // this is set to anotherTask

    // apply method
    // apply() works similarly to call(), but instead of passing arguments as a list, you pass them as an array
    toDo.showTask.apply(anotherTask, ["New task details"])

    // bind method
    // bind() doesn't immediately execute the function. Instead, it returns a new function where this is permanently set to the provided object, and you can call that new function later with arguments.
    const boundShowTask = toDo.showTask.bind(anotherTask);  // Using bind() to permanently bind `this` to `anotherTask`
    // Calling the bound function
    boundShowTask("Bounded Task details: ");
 */

    

    // Collect form data
    const task = document.getElementById("task").value;
    const priority = document.getElementById("priority").value;

    // Create a task object
    const taskData = { task, priority, timestamp: new Date().toISOString() };

    // 2. JSON.stringify to store task data
    /// `JSON.stringify` converts a JavaScript object into a JSON string representation. ///
    const jsonTaskData = JSON.stringify(taskData);
    console.log("Task Data (String):", jsonTaskData);

    // 3. JSON.parse to retrieve task data
    /// `JSON.parse` converts a JSON string back into a JavaScript object. ///
    const parsedTaskData = JSON.parse(jsonTaskData);
    console.log("Task Data (JSON):", parsedTaskData);

    // 4. Destructuring
    const { task: taskName, priority: taskPriority } = parsedTaskData;
    console.log("Task Name:", taskName);
    console.log("Task Priority:", taskPriority);

    // 5. Spread operator to add an ID field
    const updatedTask = { ...parsedTaskData, id: `task-${taskCounter()}` };
    console.log("Updated Task:", updatedTask);



    // Add task to the task list
    // addTaskToUI(updatedTask); 
    
    
    // PROMISES
    // Save the task asynchronously
    try {
        const serverResponse = await saveTaskToServer(updatedTask);
        console.log(serverResponse);
        
        // Add task to the UI only after saving successfully
        addTaskToUI(updatedTask);
        alert("Task added successfully!");
    } catch (error) {
        console.error(error);
        alert(error);
    }
    

    // Clear form inputs
    document.getElementById("todoForm").reset();

});

// Function to add a task to the UI
const addTaskToUI = (taskData) => {
    const { task, priority, id } = taskData;

    // Create list item
    const listItem = document.createElement("li");
    listItem.setAttribute("id", id);
    listItem.textContent = `Task: ${task} | Priority: ${priority}`;

    // Add a delete button
    const deleteButton = document.createElement("button");
    deleteButton.textContent = "Delete";
    deleteButton.onclick = handleDelete.bind(null, id); // Using `bind`

    // Append delete button to the list item
    listItem.appendChild(deleteButton);

    // Append list item to the task list
    document.getElementById("taskList").appendChild(listItem);
};

// 7. Using call, apply, and bind for task deletion
const handleDelete = function (id) {
    const taskElement = document.getElementById(id);
    console.log(`Deleting task: ${id}`);
    taskElement.remove();
};

/* 
// 8. Variable scope examples
if (true) {
    var exampleVar = "This is var"; // Function-scoped
    let exampleLet = "This is let"; // Block-scoped
    const exampleConst = "This is const"; // Block-scoped

    console.log(exampleVar); // Accessible here
    console.log(exampleLet); // Accessible here
    console.log(exampleConst); // Accessible here
}
console.log(exampleVar); // Accessible outside block (var)
// console.log(exampleLet); // Uncaught ReferenceError
// console.log(exampleConst); // Uncaught ReferenceError
 */