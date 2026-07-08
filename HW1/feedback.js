// ===== CONCEPT 1: STRICT MODE =====
"use strict"; // enables strict mode and enforces stricter parsing

// ===== CONCEPT 2: FUNCTIONS - REGULAR VS ARROW =====

// Regular function (traditional way)
function normalValidateForm() {
    const name = document.getElementById("studentName").value.trim();
    const email = document.getElementById("studentEmail").value.trim();
    const feedback = document.getElementById("feedbackMessage").value;

    if (!name || !email || !feedback) {
        alert("All fields are required!");
        return false;
    }
    console.log("Form validation successful.")
    return true;
}

/* "Arrow functions are:"

1. Shorter to write- no need for the word 'function'
2. Modern JavaScript - used everywhere in React, Node.js, etc.
3. Different 'this' behavior - they keep the same 'this' from where they're created

'this' is like a pointer that says "which object am I talking about right now?"

 Regular functions: 'this' changes based on HOW the function is called
 Arrow functions: 'this' stays the same as WHERE the function was created, it never changes

*/

// Arrow function (modern way) - does the same thing as above

// This function checks if all fields are filled out.
// - "document.getElementById finds the HTML element by its ID"
// - "dot value gets whatever the user typed in"
// - "dot trim removes any extra spaces"
// - "The if statement checks - if any field is empty, show an alert and return false"
const validateForm = () => {
    const name = document.getElementById("studentName").value.trim();
    const email = document.getElementById("studentEmail").value.trim();
    const feedback = document.getElementById("feedbackMessage").value;

    if (!name || !email || !feedback) {
        alert("All fields are required!");
        return false;
    }
    return true;
};

// ===== CONCEPT 3: CLOSURES =====
// Closure to track the total number of feedback submissions
// Closure allows function to access variables from its outer (enclosing) function
const feedbackCounter = (() => {
    let count = 0;
    return () => ++count;
})();

// ===== CONCEPT 4: PROMISES AND ASYNC/AWAIT =====
// Think of a Promise like ordering food at a restaurant:"

// 1. You place an order - that's creating the promise
// 2. You wait - that's the 'pending' state
// 3. Either you get your food - that's 'resolved/fulfilled'
// 4. Or they tell you it's not available - that's 'rejected'

// Simulate an asynchronous operation (e.g., saving feedback to a server)
const saveFeedbackToServer = (feedbackData) => {
    /// A Promise in JavaScript is an object that represents the eventual completion (or failure) of an asynchronous operation///
    return new Promise((resolve, reject) => {
        console.log("Saving feedback to server...");
        setTimeout(() => {
            // Always resolve successfully since no success rate is needed
            resolve(`Feedback from "${feedbackData.name}" saved successfully!`);
        }, 2000); // Simulate a 2-second delay
    });
};

// ===== CONCEPT 5: EVENT LISTENERS =====
// Add an event listener to the form
// Event is basically an action or occurence in the browser.
// callback function can be thought of as function that is executed when an event is triggered.

document.getElementById("feedbackForm").addEventListener("submit", async (e) => { // This tells JavaScript: 'This function will have some waiting involved
    e.preventDefault(); // Prevents the form from actually submitting (default behavior) and reloading the page
    
    // CONCEPT 6: FORM VALIDATION
    // Validate form using arrow function
    if (!validateForm()) return;

    // CONCEPT 7: COLLECTING FORM DATA
    // Collect form data
    const name = document.getElementById("studentName").value;
    const email = document.getElementById("studentEmail").value;
    const feedback = document.getElementById("feedbackMessage").value;

    // Create a feedback object
    const feedbackData = { name, email, feedback, timestamp: new Date().toISOString() };

    // CONCEPT 8: JSON OPERATIONS
    // JSON is like a universal language for data. All web applications use it.
    // JSON.stringify converts our JavaScript objects into text that can be stored or sent.
    // JSON.parse converts that text back into JavaScript objects we can use.
    const jsonFeedbackData = JSON.stringify(feedbackData);
    console.log("Feedback Data (String):", jsonFeedbackData);

    // JSON.parse to retrieve feedback data
    /// `JSON.parse` converts a JSON string back into a JavaScript object. ///
    const parsedFeedbackData = JSON.parse(jsonFeedbackData);
    console.log("Feedback Data (JSON):", parsedFeedbackData);

    // CONCEPT 9: DESTRUCTURING
    // This is a fancy way to extract values from an object. 
    // Instead of writing parsedFeedbackData.name over and over, we can pull the values out directly and give them new names if we want.
    const { name: studentName, email: studentEmail, feedback: feedbackRating } = parsedFeedbackData;
    console.log("Student Name:", studentName);
    console.log("Student Email:", studentEmail);
    console.log("Feedback Rating:", feedbackRating);

    // CONCEPT 10: SPREAD OPERATOR + CLOSURES IN ACTION
    // three dots copy everything from the original object and let us add new fields.
    const currentCount = feedbackCounter();
    const updatedFeedback = { ...parsedFeedbackData, id: `feedback-${currentCount}` };
    console.log("Feedback Counter:", currentCount);
    console.log("Updated Feedback:", updatedFeedback);

    // CONCEPT 11: PROMISES IN ACTION
    // Save the feedback asynchronously
    try {
        const serverResponse = await saveFeedbackToServer(updatedFeedback);
        console.log(serverResponse);
        
        // Add feedback to the UI only after saving successfully
        addFeedbackToUI(updatedFeedback);
        alert("Feedback submitted successfully!");
    } catch (error) {
        console.error(error);
        alert(error);
    }

    // Clear form inputs
    document.getElementById("feedbackForm").reset();
});

// ===== HELPER FUNCTION FOR UI =====
// Function to add a feedback to the UI
const addFeedbackToUI = (feedbackData) => {
    const { name, email, feedback, id } = feedbackData;

    // Create list item
    const listItem = document.createElement("li");
    listItem.setAttribute("id", id);
    listItem.textContent = `Name: ${name} | Email: ${email} | Feedback: ${feedback}`;

    // Add a delete button
    const deleteButton = document.createElement("button");
    deleteButton.textContent = "Delete";
    deleteButton.onclick = handleDelete.bind(null, id); // Using `bind`

    // Append delete button to the list item
    listItem.appendChild(deleteButton);

    // Append list item to the feedback list
    document.getElementById("feedbackList").appendChild(listItem);
};

// Using call, apply, and bind for feedback deletion
const handleDelete = function (id) {
    const feedbackElement = document.getElementById(id);
    console.log(`Deleting feedback: ${id}`);
    feedbackElement.remove();
};

/* 
// ===== BONUS CONCEPTS =====

// Normal Function Vs Arrow Function - THIS keyword example
const formValidator = {
    name: "John Doe",
    feedback: "Excellent",
    
    // Regular function
    regularValidateForm: function() {
        console.log("Inside regular function, this refers to:", this);
    },
    
    // Arrow function
    arrowValidateForm: () => {
        console.log("Inside arrow function, this refers to:", this);
    }
};

// call, apply and bind examples
const feedbackObj = {
    name: "Jane Smith",
    feedback: "Good",
    showFeedback: function (msg) {
        console.log(msg + this.feedback + " from: " + this.name);
    }
}

// call method
// call() lets you immediately invoke the function with a specified this value, and pass arguments as a list.
const anotherFeedback = {name: "Bob Wilson", feedback: "Excellent"}
feedbackObj.showFeedback.call(anotherFeedback, "Feedback details: ") // this is set to anotherFeedback

// apply method
// apply() works similarly to call(), but instead of passing arguments as a list, you pass them as an array
feedbackObj.showFeedback.apply(anotherFeedback, ["New feedback details: "])

// bind method
// bind() doesn't immediately execute the function. Instead, it returns a new function where this is permanently set to the provided object, and you can call that new function later with arguments.
const boundShowFeedback = feedbackObj.showFeedback.bind(anotherFeedback);
boundShowFeedback("Bounded Feedback details: ");

// Variable scope examples
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