/**
 * BeamNG Blind Accessibility - UI State Capture App
 *
 * This AngularJS app monitors the BeamNG UI for accessibility-relevant events
 * and sends them to the game engine extension via bngApi.
 */

angular.module('beamng.apps').directive('blindAccessibility', ['bngApi', '$timeout', '$document',
function(bngApi, $timeout, $document) {
    return {
        restrict: 'E',
        template: '<div class="blind-accessibility-monitor"></div>',
        replace: true,
        link: function(scope, element, attrs) {

            // Configuration
            var config = {
                enabled: true,
                pollInterval: 100,  // ms between DOM checks
                debounceTime: 50,   // ms to debounce rapid changes
            };

            // State tracking
            var currentFocusedElement = null;
            var currentMenuName = '';
            var currentMenuItems = [];
            var currentSelectedIndex = -1;
            var lastAnnouncedText = '';
            var debounceTimer = null;
            var pollTimer = null;

            /**
             * Send accessibility event to game engine extension
             */
            function sendEvent(eventData) {
                if (!config.enabled) return;
                bngApi.engineLua('extensions.blindAccessibility.onAccessibilityEvent(' +
                    bngApi.serializeToLua(eventData) + ')');
            }

            /**
             * Debounced send to avoid rapid-fire announcements
             */
            function sendEventDebounced(eventData) {
                if (debounceTimer) {
                    $timeout.cancel(debounceTimer);
                }
                debounceTimer = $timeout(function() {
                    sendEvent(eventData);
                }, config.debounceTime);
            }

            /**
             * Extract text content from an element
             */
            function getElementText(el) {
                if (!el) return '';

                // Try various attributes that might contain accessible text
                var text = el.getAttribute('aria-label') ||
                           el.getAttribute('title') ||
                           el.getAttribute('data-label') ||
                           el.getAttribute('ng-bind') ||
                           el.textContent ||
                           el.innerText ||
                           '';

                // Clean up whitespace
                text = text.replace(/\s+/g, ' ').trim();

                return text;
            }

            /**
             * Get menu items from a menu container
             */
            function getMenuItems(menuContainer) {
                if (!menuContainer) return [];

                var items = [];
                var itemElements = menuContainer.querySelectorAll(
                    '.menu-item, .list-item, [role="menuitem"], [role="option"], ' +
                    '.bng-button, .vehicle-item, .level-item, li'
                );

                itemElements.forEach(function(el, index) {
                    var text = getElementText(el);
                    if (text) {
                        items.push({
                            index: index + 1,
                            text: text,
                            element: el
                        });
                    }
                });

                return items;
            }

            /**
             * Find the currently focused/selected item in a list
             */
            function findSelectedItem(items) {
                for (var i = 0; i < items.length; i++) {
                    var el = items[i].element;
                    if (el.classList.contains('selected') ||
                        el.classList.contains('focused') ||
                        el.classList.contains('active') ||
                        el.classList.contains('highlight') ||
                        el.getAttribute('aria-selected') === 'true' ||
                        el === document.activeElement) {
                        return i;
                    }
                }
                return -1;
            }

            /**
             * Detect current menu context
             */
            function detectMenuContext() {
                // Look for common menu containers in BeamNG UI
                var menuSelectors = [
                    '.mainmenu',
                    '.menu-container',
                    '.modal-dialog',
                    '.dialog-container',
                    '.vehicle-selector',
                    '.level-selector',
                    '.options-menu',
                    '[role="menu"]',
                    '[role="dialog"]',
                    '.bng-modal'
                ];

                for (var i = 0; i < menuSelectors.length; i++) {
                    var menu = document.querySelector(menuSelectors[i] + ':not([style*="display: none"])');
                    if (menu && menu.offsetParent !== null) {
                        return {
                            element: menu,
                            name: menu.getAttribute('data-menu-name') ||
                                  menu.getAttribute('aria-label') ||
                                  menu.className.split(' ')[0] ||
                                  'Menu'
                        };
                    }
                }

                return null;
            }

            /**
             * Handle focus change
             */
            function handleFocusChange(newFocusedElement) {
                if (newFocusedElement === currentFocusedElement) return;

                currentFocusedElement = newFocusedElement;

                if (!newFocusedElement) return;

                var text = getElementText(newFocusedElement);
                if (!text || text === lastAnnouncedText) return;

                lastAnnouncedText = text;

                // Determine context
                var menuContext = detectMenuContext();
                var items = menuContext ? getMenuItems(menuContext.element) : [];
                var selectedIndex = findSelectedItem(items);

                sendEventDebounced({
                    type: 'menuItemFocused',
                    text: text,
                    index: selectedIndex + 1,
                    total: items.length,
                    menuName: menuContext ? menuContext.name : ''
                });
            }

            /**
             * Poll for UI changes (backup for events we might miss)
             */
            function pollUIState() {
                if (!config.enabled) return;

                // Check for active element changes
                var activeElement = document.activeElement;
                if (activeElement && activeElement !== document.body) {
                    handleFocusChange(activeElement);
                }

                // Check for selected items in menus
                var menuContext = detectMenuContext();
                if (menuContext) {
                    var items = getMenuItems(menuContext.element);
                    var selectedIndex = findSelectedItem(items);

                    if (selectedIndex !== currentSelectedIndex && selectedIndex >= 0) {
                        currentSelectedIndex = selectedIndex;
                        var selectedItem = items[selectedIndex];

                        if (selectedItem && selectedItem.text !== lastAnnouncedText) {
                            lastAnnouncedText = selectedItem.text;

                            sendEvent({
                                type: 'menuItemFocused',
                                text: selectedItem.text,
                                index: selectedIndex + 1,
                                total: items.length,
                                menuName: menuContext.name
                            });
                        }
                    }
                }

                // Schedule next poll
                pollTimer = $timeout(pollUIState, config.pollInterval);
            }

            /**
             * Handle keyboard navigation
             */
            function handleKeydown(event) {
                if (!config.enabled) return;

                var key = event.key || event.keyCode;

                // Navigation keys that should trigger announcements
                var navKeys = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight',
                               'Tab', 'Enter', 'Escape', 'Home', 'End',
                               38, 40, 37, 39, 9, 13, 27, 36, 35];

                if (navKeys.indexOf(key) !== -1) {
                    // Small delay to let the UI update first
                    $timeout(function() {
                        var activeElement = document.activeElement;
                        handleFocusChange(activeElement);
                    }, 50);
                }

                // Escape key - announce menu closed
                if (key === 'Escape' || key === 27) {
                    $timeout(function() {
                        var menuContext = detectMenuContext();
                        if (!menuContext) {
                            sendEvent({ type: 'menuClosed' });
                        }
                    }, 100);
                }
            }

            /**
             * Set up mutation observer for dynamic content
             */
            function setupMutationObserver() {
                var observer = new MutationObserver(function(mutations) {
                    mutations.forEach(function(mutation) {
                        // Check for dialog/modal appearances
                        if (mutation.type === 'childList') {
                            mutation.addedNodes.forEach(function(node) {
                                if (node.nodeType === Node.ELEMENT_NODE) {
                                    // Check if it's a dialog
                                    if (node.classList &&
                                        (node.classList.contains('modal') ||
                                         node.classList.contains('dialog') ||
                                         node.getAttribute('role') === 'dialog')) {

                                        var title = node.querySelector('.modal-title, .dialog-title, h1, h2');
                                        var content = node.querySelector('.modal-body, .dialog-content, p');

                                        sendEvent({
                                            type: 'dialog',
                                            title: title ? getElementText(title) : 'Dialog',
                                            content: content ? getElementText(content) : ''
                                        });
                                    }

                                    // Check if it's a menu
                                    if (node.classList &&
                                        (node.classList.contains('menu') ||
                                         node.getAttribute('role') === 'menu')) {

                                        sendEvent({
                                            type: 'menuOpened',
                                            name: getElementText(node) || 'Menu'
                                        });
                                    }
                                }
                            });
                        }
                    });
                });

                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });

                return observer;
            }

            /**
             * Initialize the accessibility monitor
             */
            function init() {
                console.log('[BlindAccessibility] UI monitor initializing...');

                // Set up event listeners
                document.addEventListener('keydown', handleKeydown, true);
                document.addEventListener('focusin', function(e) {
                    handleFocusChange(e.target);
                }, true);

                // Set up mutation observer
                var observer = setupMutationObserver();

                // Start polling
                pollUIState();

                // Notify extension that UI app is ready
                sendEvent({
                    type: 'status',
                    text: 'UI accessibility monitor active'
                });

                console.log('[BlindAccessibility] UI monitor initialized');

                // Cleanup on scope destroy
                scope.$on('$destroy', function() {
                    config.enabled = false;
                    document.removeEventListener('keydown', handleKeydown, true);
                    if (pollTimer) {
                        $timeout.cancel(pollTimer);
                    }
                    if (debounceTimer) {
                        $timeout.cancel(debounceTimer);
                    }
                    observer.disconnect();
                    console.log('[BlindAccessibility] UI monitor destroyed');
                });
            }

            // Initialize after a short delay to ensure DOM is ready
            $timeout(init, 500);
        }
    };
}]);

// App registration info for BeamNG
angular.module('beamng.apps').config(['$compileProvider', function($compileProvider) {
    // Register the app
}]);
