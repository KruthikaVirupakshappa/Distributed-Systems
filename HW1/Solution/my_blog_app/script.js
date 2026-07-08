const createSubmissionCounter = () => {
  let count = 0;
  return () => {
    count += 1;
    return count;
  };
};

const incrementSubmissionCount = createSubmissionCounter();

const validateForm = () => {
    const contentValue = document.getElementById("content").value.trim();
    const agreeChecked = document.getElementById("agree").checked;
  
    if (contentValue.length <= 25) {
    alert("Blog content should be more than 25 characters");
    return false;
    }

    if (!agreeChecked) {
        alert("You must agree to the terms and conditions");
        return false;
        }   

    return true;
};

const form = document.querySelector("form");
form.addEventListener("submit", (event) => {
    event.preventDefault();

    if (!validateForm()) return;

    const formData = new FormData(form);
    const dataObj = Object.fromEntries(formData.entries());

    const jsonString = JSON.stringify(dataObj);
    console.log("JSON String:", jsonString);

    const parsedObj = JSON.parse(jsonString);

    const{title, email} = parsedObj;
    console.log("Title:", title);
    console.log("Email:", email);

    const updatedObj ={
    ...parsedObj,
    submissionDate: new Date().toISOString()
    };
    console.log("Updated Object:", updatedObj);

    const submissionCount = incrementSubmissionCount();
    console.log("Submission Count:", submissionCount);

    alert("Form submitted successfully!");
});



