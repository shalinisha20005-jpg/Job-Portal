function searchJobs() {
    const keyword = document.querySelector(
        '.search-box input:first-child'
    ).value.trim();

    const location = document.querySelector(
        '.search-box input:nth-child(2)'
    ).value.trim();

    const params = new URLSearchParams();

    if (keyword) params.set("keyword", keyword);
    if (location) params.set("location", location);

    window.location.href = "/jobs?" + params.toString();
}