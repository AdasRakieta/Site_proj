/**
 * Minimal Dragula fallback for room column reordering
 * Provides basic drag and drop functionality when Dragula CDN is not available
 */

console.log('dragula-fallback.js loaded');

if (typeof dragula === 'undefined') {
    console.log('Dragula not available, using fallback implementation');
    
    window.dragula = function(containers, options) {
        options = options || {};
        const instance = {
            events: {},
            containers: containers || [],
            options: options,
            
            on: function(eventName, callback) {
                this.events[eventName] = this.events[eventName] || [];
                this.events[eventName].push(callback);
                return this;
            },
            
            emit: function(eventName) {
                const args = Array.prototype.slice.call(arguments, 1);
                if (this.events[eventName]) {
                    this.events[eventName].forEach(callback => {
                        callback.apply(this, args);
                    });
                }
            },
            
            destroy: function() {
                this.containers.forEach(container => {
                    this.removeContainerEvents(container);
                });
                this.events = {};
            },
            
            setupContainer: function(container) {
                const self = this;
                
                // Make all draggable elements draggable
                this.updateDraggableElements(container);
                
                // Handle dragstart
                container.addEventListener('dragstart', function(e) {
                    if (!self.canMove(e.target, container, e.target)) return;
                    
                    e.dataTransfer.effectAllowed = 'move';
                    e.dataTransfer.setData('text/html', e.target.outerHTML);
                    self.draggedElement = e.target;
                    self.sourceContainer = container;
                    
                    e.target.style.opacity = '0.5';
                });
                
                // Handle dragend
                container.addEventListener('dragend', function(e) {
                    if (e.target === self.draggedElement) {
                        e.target.style.opacity = '';
                    }
                });
                
                // Handle dragover - allow drop
                container.addEventListener('dragover', function(e) {
                    e.preventDefault();
                    e.dataTransfer.dropEffect = 'move';
                });
                
                // Handle drop
                container.addEventListener('drop', function(e) {
                    e.preventDefault();
                    
                    if (!self.draggedElement) return;
                    
                    const dropTarget = e.target;
                    const draggable = self.findDraggableParent(dropTarget);
                    
                    if (draggable && draggable !== self.draggedElement) {
                        // Determine position based on mouse position
                        const rect = draggable.getBoundingClientRect();
                        const isHorizontal = self.options.direction === 'horizontal';
                        const insertBefore = isHorizontal ? 
                            (e.clientX < rect.left + rect.width / 2) :
                            (e.clientY < rect.top + rect.height / 2);
                        
                        if (insertBefore) {
                            container.insertBefore(self.draggedElement, draggable);
                        } else {
                            container.insertBefore(self.draggedElement, draggable.nextSibling);
                        }
                    } else if (self.isValidDropTarget(dropTarget)) {
                        // Drop at end of container
                        container.appendChild(self.draggedElement);
                    }
                    
                    // Emit drop event
                    self.emit('drop', self.draggedElement, container, self.sourceContainer, null);
                    
                    self.draggedElement.style.opacity = '';
                    self.draggedElement = null;
                    self.sourceContainer = null;
                });
            },
            
            updateDraggableElements: function(container) {
                const elements = container.children;
                for (let i = 0; i < elements.length; i++) {
                    const element = elements[i];
                    if (this.canMove(element, container, element)) {
                        element.draggable = true;
                        element.style.cursor = 'move';
                    }
                }
            },
            
            findDraggableParent: function(element) {
                while (element && element.parentNode !== this.containers[0]) {
                    if (element.draggable) {
                        return element;
                    }
                    element = element.parentNode;
                }
                return null;
            },
            
            isValidDropTarget: function(element) {
                return this.containers.includes(element) || 
                       this.containers.some(container => container.contains(element));
            },
            
            canMove: function(el, container, handle) {
                if (this.options.moves) {
                    return this.options.moves(el, container, handle);
                }
                return true;
            },
            
            removeContainerEvents: function(container) {
                // Create new container to remove all event listeners
                if (container && container.parentNode) {
                    const newContainer = container.cloneNode(true);
                    container.parentNode.replaceChild(newContainer, container);
                }
            }
        };
        
        // Setup drag and drop for each container
        instance.containers.forEach(container => {
            instance.setupContainer(container);
        });
        
        return instance;
    };
} else {
    console.log('Dragula library is available');
}