
const tabButtons = document.querySelectorAll('.tab-button');
const productContainers = document.querySelectorAll('.product-container');

tabButtons.forEach(button => {
  button.addEventListener('click', () => {
    const categoryId = button.getAttribute('data-product');
    setActiveTab(button);
    showProductContainer(categoryId);
  });
});

function setActiveTab(activeButton) {
  tabButtons.forEach(button => {
    button.classList.remove('active');
  });
  activeButton.classList.add('active');
}

function showProductContainer(categoryId) {
  productContainers.forEach(container => {
    container.classList.remove('active');
  });
  const productContainer = document.getElementById(categoryId + '-product');
  productContainer.classList.add('active');
}
