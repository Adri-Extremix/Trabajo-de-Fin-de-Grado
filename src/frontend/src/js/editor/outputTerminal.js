import $ from 'jquery';

/**
 * Updates the content of the Terminal div
 * @param {string} content - The content to display in the terminal
 */
function updateTerminal(content) {
    $('#Output').html(content);
}
// Export the functions if using module system
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = { updateTerminal};
}