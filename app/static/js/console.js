const host = window.location.origin;

const jumpTo = (time) => {
  const videoPlayer = document.getElementById("videoPlayer");
  videoPlayer.currentTime = time;
  videoPlayer.play();
};

const initVideo = () => {
  document
    .getElementById("videoPlayer")
    .addEventListener("loadedmetadata", () => {
      console.log("Metadata loaded");
    });

  document.getElementById("videoPlayer").addEventListener("seeked", () => {
    console.log("Seek operation completed");
    videoPlayer.play();
  });
};

const createInferenceItem = (inference) => {
  const buttonStyle =
    inference.status === "SUCCESS"
      ? "success"
      : inference.status === "STARTED"
      ? "info"
      : "danger";
  return `
      <li class="btn btn-outline-light list-group-item d-flex justify-content-between align-items-center" data-uuid="${inference.inference_uuid}">
          <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close" onclick="deleteVideo('${inference.inference_uuid}')"></button>
          <div class="ms-2 me-auto">
              <div class="fw-bold">Date: ${inference.inference_datetime}</div>
              Inference ID: ${inference.inference_uuid}
          </div>
          <span class="badge text-bg-${buttonStyle} rounded-pill">${inference.status}</span>
      </li>
  `;
};

const renderInferenceList = (data) => {
  const videoList = document.getElementById("videoList");
  videoList.innerHTML = data.inference_results
    .map(createInferenceItem)
    .join("");
  addClickEventListeners();
};

const addClickEventListeners = () => {
  const videoList = document.getElementById("videoList");
  const listItems = videoList.getElementsByClassName("list-group-item");
  Array.from(listItems).forEach((li) => {
    li.addEventListener("click", () => {
      const uuid = li.getAttribute("data-uuid");
      updateVideoSource(uuid);
      setActiveItem(li);
    });
  });
};

const setActiveItem = (activeLi) => {
  const videoList = document.getElementById("videoList");
  const listItems = videoList.getElementsByClassName("list-group-item");
  Array.from(listItems).forEach((li) => li.classList.remove("active"));
  activeLi.classList.add("active");
};

const updateVideoSource = (uuid) => {
  const videoUrl = `${host}/v1/api/video/preprocessed?uuid=${uuid}`;
  const videoSource = document.getElementById("videoSource");
  videoSource.src = videoUrl;
  document.getElementById("videoPlayer").load();
};

function deleteVideo(uuid) {
  fetch(`${host}/v1/api/inference?uuid=${uuid}`, { method: "DELETE" })
    .then((response) => response.json())
    .then((data) => {
      document.querySelector(`li[data-uuid="${uuid}"]`).remove();
    })
    .catch((error) => console.error("Error deleting video:", error));
}

const initVideoList = () => {
  fetch(`${host}/v1/api/inference/all`)
    .then((response) => response.json())
    .then((data) => {
      if (data && data.inference_results) {
        renderInferenceList(data);
      } else {
        console.error("Invalid response structure:", data);
      }
    })
    .catch((error) => console.error("Error fetching inference jobs:", error));
};

const generateAlert = () => {
  const alertPlaceholder = document.getElementById("liveAlertPlaceholder");
  const appendAlert = (message, type) => {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = [
      `<div class="alert alert-${type} alert-dismissible" role="alert">`,
      `   <div>${message}</div>`,
      `   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>`,
      "</div>",
    ].join("");

    alertPlaceholder.append(wrapper);
  };
  document
    .getElementById("uploadForm")
    .addEventListener("submit", function (event) {
      event.preventDefault();
      const formFile = document.getElementById("formFile").files[0];
      if (formFile) {
        const formData = new FormData();
        formData.append("inference_data", formFile);
        fetch(`${host}/v1/api/inference`, {
          method: "POST",
          body: formData,
        })
          .then((response) => response.json())
          .then((data) => {
            console.log("File uploaded successfully:", data);
            initVideoList();
            appendAlert("File uploaded successfully", "success");
          })
          .catch((error) => console.error("Error uploading file:", error));
      }
    });
};

document.addEventListener("DOMContentLoaded", () => {
  initVideoList();
  initVideo();
  generateAlert();
});
