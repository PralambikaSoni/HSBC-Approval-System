document.addEventListener("DOMContentLoaded", function() {
    const searchName = document.getElementById('search-name');
    const searchDept = document.getElementById('search-dept');
    const searchRole = document.getElementById('search-role');
    const searchBtn = document.getElementById('trigger-search');
    const resultsContainer = document.getElementById('search-results');
    const selectedContainer = document.getElementById('selected-approvers');
    const noApproversMsg = document.getElementById('no-approvers-msg');
    const submitBtn = document.getElementById('submit-request-btn');
    const form = document.getElementById('create-request-form');

    let selectedApprovers = new Set(); // store IDs

    function performSearch() {
        const name = encodeURIComponent(searchName.value);
        const dept = encodeURIComponent(searchDept.value);
        const role = encodeURIComponent(searchRole.value);

        if (!name && !dept && !role) {
            resultsContainer.innerHTML = '<div style="font-size:12px; color:#666; text-align:center;">Enter a search term.</div>';
            return;
        }

        resultsContainer.innerHTML = '<div style="font-size:12px; color:#666; text-align:center;">Searching...</div>';

        fetch(`/search/approvers?name=${name}&department=${dept}&role=${role}`)
            .then(response => response.json())
            .then(data => {
                resultsContainer.innerHTML = '';
                if (data.length === 0) {
                    resultsContainer.innerHTML = '<div style="font-size:12px; color:#666; text-align:center;">No match found.</div>';
                    return;
                }

                data.forEach(user => {
                    const isSelected = selectedApprovers.has(user.id);

                    const div = document.createElement('div');
                    div.style.padding = '10px';
                    div.style.border = '1px solid #eee';
                    div.style.borderRadius = '5px';
                    div.style.marginBottom = '5px';
                    div.style.cursor = 'pointer';
                    div.style.background = '#fafafa';
                    div.style.display = 'flex';
                    div.style.alignItems = 'center';
                    div.style.gap = '10px';
                    
                    div.innerHTML = `
                        <input type="checkbox" id="chk-${user.id}" ${isSelected ? 'checked' : ''} style="cursor:pointer; width:16px; height:16px;" />
                        <div style="flex:1;">
                            <div style="font-weight:bold; font-size:14px;">${user.full_name} <span style="font-weight:normal; color:#888;">(${user.employee_id})</span></div>
                            <div style="font-size:12px; color:#666;">${user.role} - ${user.department}</div>
                        </div>
                    `;

                    div.addEventListener('click', (e) => {
                        // Avoid toggling twice if the user clicked exactly on the checkbox
                        if (e.target.tagName !== 'INPUT') {
                            const chk = div.querySelector('input');
                            chk.checked = !chk.checked;
                        }
                        
                        const chk = div.querySelector('input');
                        if (chk.checked) {
                            selectApprover(user);
                        } else {
                            unselectApprover(user.id);
                        }
                    });
                    resultsContainer.appendChild(div);
                });
            })
            .catch(err => {
                resultsContainer.innerHTML = '<div style="font-size:12px; color:red; text-align:center;">Error fetching data.</div>';
            });
    }

    function selectApprover(user) {
        if (selectedApprovers.has(user.id)) return;
        selectedApprovers.add(user.id);

        noApproversMsg.style.display = 'none';

        const chip = document.createElement('div');
        chip.id = `approver-${user.id}`;
        chip.style.background = '#e1f5fe';
        chip.style.border = '1px solid #b3e5fc';
        chip.style.padding = '10px';
        chip.style.borderRadius = '5px';
        chip.style.display = 'flex';
        chip.style.flexDirection = 'column';
        chip.style.gap = '5px';

        chip.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="font-size:13px;">${user.full_name} (${user.role})</strong>
                <span class="remove-approver" style="cursor:pointer; color:red; font-size:16px;">&times;</span>
            </div>
            <input type="hidden" name="approver_ids" value="${user.id}">
            <textarea name="note_${user.id}" placeholder="Optional note for ${user.full_name}..." style="width:100%; font-size:12px; padding:5px; border:1px solid #ccc; border-radius:3px; resize:vertical;"></textarea>
        `;

        chip.querySelector('.remove-approver').addEventListener('click', () => {
            unselectApprover(user.id);
        });

        selectedContainer.appendChild(chip);
        
        // Ensure checkbox is checked if it's currently rendered in the results
        const chk = document.getElementById(`chk-${user.id}`);
        if(chk) chk.checked = true;
        
        enableSubmit();
    }

    function unselectApprover(userId) {
        selectedApprovers.delete(userId);
        
        const chip = document.getElementById(`approver-${userId}`);
        if(chip) chip.remove();
        
        if (selectedApprovers.size === 0) {
            noApproversMsg.style.display = 'block';
            disableSubmit();
        }
        
        // Uncheck the checkbox if it's currently in the results
        const chk = document.getElementById(`chk-${userId}`);
        if(chk) chk.checked = false;
    }

    function enableSubmit() {
        submitBtn.disabled = false;
        submitBtn.style.background = 'var(--primary)';
        submitBtn.textContent = 'Submit Request';
    }

    function disableSubmit() {
        submitBtn.disabled = true;
        submitBtn.style.background = '#bdc3c7';
        submitBtn.textContent = 'Select at least 1 approver to submit';
    }

    searchBtn.addEventListener('click', performSearch);
    
    // Auto trigger search on keyup if length >= 3
    searchName.addEventListener('keyup', (e) => {
        if (searchName.value.length >= 3 || e.key === 'Enter') {
            if (e.key === 'Enter') e.preventDefault(); // prevent form submission
            performSearch();
        }
    });

    // Make sure form doesn't submit implicitly on hit enter in search
    form.addEventListener('keydown', function(event) {
        if(event.key === "Enter" && event.target.tagName !== 'TEXTAREA') {
            event.preventDefault();
            return false;
        }
    });

    // Initial load: populate with current user's department
    if (window.USER_DOMAIN) {
        // If the domain matches a select option, set it, otherwise it still works as a custom value since we send it over fetch or we can add it as an option
        let optionExists = false;
        for (let i = 0; i < searchDept.options.length; i++) {
            if (searchDept.options[i].value.toLowerCase() === window.USER_DOMAIN.toLowerCase()) {
                searchDept.selectedIndex = i;
                optionExists = true;
                break;
            }
        }
        // Even if it's not strictly an option, we can still perform search with the text, but the select dropdown might not reflect it unless we add it
        if (!optionExists && window.USER_DOMAIN) {
             const newOption = new Option(window.USER_DOMAIN, window.USER_DOMAIN, true, true);
             searchDept.add(newOption);
        }
        
        performSearch();
    }
});
