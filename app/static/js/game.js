document.addEventListener('DOMContentLoaded', function () {
    var draggables = document.querySelectorAll('.draggable');
    var blocks = document.querySelectorAll('.block, .draggable');

    function isColliding(newX, newY, draggable) {
        for (let block of blocks) {
            if (block === draggable) continue; // Skip self

            let bounds = getBounds(block);
            let draggableWidth = draggable.offsetWidth;
            let draggableHeight = draggable.offsetHeight;

            if (newX < bounds.right &&
                newX + draggableWidth > bounds.left &&
                newY < bounds.bottom &&
                newY + draggableHeight > bounds.top) {
                return true; // Collision detected
            }
        }
        return false; // No collision
    }

    function getBounds(element) {
        return element.getBoundingClientRect();
    }

    function updatePositions() {
        // Ensure calculations are within the viewport
        console.log('Updating positions');
        var block1Bounds = document.getElementById('block1').getBoundingClientRect();
        var block2Bounds = document.getElementById('block2').getBoundingClientRect();
        var spaceBetween = block2Bounds.left - block1Bounds.right;
        var centerY = window.innerHeight / 2 - (document.querySelector('.draggable').offsetHeight / 2);
        var startX = block1Bounds.right + spaceBetween / 2 - (document.querySelector('.draggable').offsetWidth / 2);

        var overlay = document.getElementById('overlay');
        overlay.style.left = `${startX}px`;
        overlay.style.top = `${centerY}px`;

        updateRelativePositions(); // Ensure relative positions are set after initial positions
    }

    function updateRelativePositions() {
        var overlay = document.getElementById('overlay');
        var overlayBounds = overlay.getBoundingClientRect();
        var block3 = document.getElementById('block3');
        var block4 = document.getElementById('block4');
        var block5 = document.getElementById('block5');
        var block6 = document.getElementById('block6');

        // 5vw to the right of the overlay for block3 and block5
        block3.style.left = `${overlayBounds.right + 5 * (window.innerWidth / 100)}px`;
        block3.style.top = `${overlayBounds.top + 5 * (window.innerWidth / 100)}px`;

        block5.style.left = `${overlayBounds.right + 5 * (window.innerWidth / 100)}px`;
        block5.style.top = `${overlayBounds.top + 15 * (window.innerWidth / 100)}px`;

        // 5vw to the left of the overlay for block4 and block6, considering its own width
        block4.style.left = `${overlayBounds.left - block4.offsetWidth - 5 * (window.innerWidth / 100)}px`;
        block4.style.top = `${overlayBounds.top - block4.offsetWidth - 15 * (window.innerWidth / 100)}px`;

        block6.style.left = `${overlayBounds.left - block6.offsetWidth - 5 * (window.innerWidth / 100)}px`;
        block6.style.top = `${overlayBounds.top - block6.offsetWidth - 5 * (window.innerWidth / 100)}px`;
    }

    function handleMouseDown(e) {
        var draggable = e.target;
        draggable.isDown = true;
        draggable.offset = [
            draggable.offsetLeft - (e.clientX || e.touches[0].clientX),
            draggable.offsetTop - (e.clientY || e.touches[0].clientY)
        ];
    }

    function handleMouseMove(e) {
        draggables.forEach(function (draggable) {
            if (!draggable.isDown) return;
            e.preventDefault();

            var newX = (e.clientX || e.touches[0].clientX) + draggable.offset[0];
            var newY = (e.clientY || e.touches[0].clientY) + draggable.offset[1];

            if (draggable.id === 'overlay') {
                logLaneAndDistance(newX);
            }

            if (!isColliding(newX, newY, draggable)) {
                draggable.style.left = newX + 'px';
                draggable.style.top = newY + 'px';
            } else {
                console.log('Collision detected, movement blocked');
            }
        });
    }

    function handleMouseUp() {
        draggables.forEach(function (draggable) {
            draggable.isDown = false;
        });
    }

    function logLaneAndDistance(newX) {
        var block1Bounds = document.getElementById('block1').getBoundingClientRect();
        var block2Bounds = document.getElementById('block2').getBoundingClientRect();
        var overlayBounds = document.getElementById('overlay').getBoundingClientRect();
        var block4Bounds = document.getElementById('block4').getBoundingClientRect();
        var spaceBetween = block2Bounds.left - block1Bounds.right;
        var laneWidth = spaceBetween / 3;

        // Determine the lane
        let lane;
        if (newX < block1Bounds.right + laneWidth) {
            console.log('Lane 1');
            lane = 1;
        } else if (newX < block1Bounds.right + 2 * laneWidth) {
            console.log('Lane 2');
            lane = 2;
        } else {
            console.log('Lane 3');
            lane = 3;
        }

        // Calculate the distance from the right edge of the overlay to the left edge of block4
        var distance = overlayBounds.top - block4Bounds.top;
        console.log('Distance to block4:', distance + 'px');
        updateERP(lane, distance)
    }

    function updateERP(lane, distance) {
        distance = distance / 2
        colour = distance > 100 ? "orange" : distance > 0 ? "red" : "green"
        var distanceText = distance > 0 ? distance + "m" : "Passed"
        document.getElementById('distance').innerText = distanceText;
        document.getElementById('distance').style.color = colour;
        document.getElementById('lane').innerText = lane;
        document.querySelectorAll('.arrows i').forEach(arrow => {
            arrow.classList.remove('active');
        });
        document.getElementById(lane).classList.add('active');
    }

    draggables.forEach(function (draggable) {
        draggable.addEventListener('mousedown', handleMouseDown, true);
        draggable.addEventListener('touchstart', handleMouseDown, true);
    });

    document.addEventListener('mousemove', handleMouseMove, true);
    document.addEventListener('mouseup', handleMouseUp, true);
    document.addEventListener('touchmove', handleMouseMove, true);
    document.addEventListener('touchend', handleMouseUp, true);

    window.addEventListener('resize', function () {
        updatePositions(); // Re-adjust positions on window resize
        updateRelativePositions(); // Ensure relative positions are re-calculated on resize
    });

    updatePositions(); // Set initial positions
});
