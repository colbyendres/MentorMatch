(() => {
  const initPillbox = () => {
    const positionCheckboxes = document.querySelectorAll('input[name="position"]');
    const matchesSelect = document.getElementById("matches");
    const pillbox = document.getElementById("pillbox");
    const dropdownTrigger = document.getElementById("matches-dropdown-trigger");

    if (!matchesSelect || !pillbox || !dropdownTrigger) {
      return;
    }

    let customDropdown = null;

    const getSelectedRole = () => {
      const checked = Array.from(positionCheckboxes).find((cb) => cb.checked);
      return checked ? checked.value : null;
    };

    const getEligibleOptions = () => {
      const role = getSelectedRole();
      if (!role) return [];

      return Array.from(matchesSelect.options).filter((option) => {
        const optionRole = option.dataset.role;
        return optionRole && optionRole !== role && !option.selected;
      });
    };

    const renderPills = (role) => {
      const pillColor = role === "mentor" ? "bg-indigo-800" : "bg-fuchsia-700";
      const selected = Array.from(matchesSelect.selectedOptions);
      pillbox.innerHTML = selected
        .map(
          (option) =>
            `<div class="inline-flex items-center gap-2 ${pillColor} text-white px-3 py-1 rounded-full text-sm font-medium" data-value="${option.value}">
               ${option.textContent}
               <button type="button" class="remove-pill hover:text-red-200 font-bold" data-value="${option.value}">×</button>
             </div>`
        )
        .join("");

      // Add event listeners to remove buttons
      document.querySelectorAll(".remove-pill").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          e.preventDefault();
          const value = btn.dataset.value;
          const option = Array.from(matchesSelect.options).find(
            (o) => o.value === value
          );
          if (option) {
            option.selected = false;
            renderPills(role);
          }
        });
      });
    };

    const closeDropdown = () => {
      if (customDropdown) {
        customDropdown.remove();
        customDropdown = null;
      }
    };

    const openDropdown = () => {
      closeDropdown();

      const eligibleOptions = getEligibleOptions();
      
      if (eligibleOptions.length === 0) {
        return;
      }

      const role = getSelectedRole()
      
      // Determine BG/pill color of potential matches
      const matchColor = role === "mentee" ? "bg-indigo-200" : "bg-fuchsia-200";
      const matchRole = role === "mentee" ? "mentor" : "mentee";

      // Create custom dropdown
      customDropdown = document.createElement("div");
      customDropdown.className = "absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto";
      eligibleOptions.forEach((option) => {
        const item = document.createElement("div");
        item.className = `px-4 py-2 hover:${matchColor} cursor-pointer text-gray-800`;
        item.textContent = option.textContent;
        item.addEventListener("click", () => {
          option.selected = true;
          renderPills(matchRole);
          closeDropdown();
        });
        customDropdown.appendChild(item);
      });

      // Position dropdown relative to trigger button
      const triggerRect = dropdownTrigger.getBoundingClientRect();
      const container = dropdownTrigger.parentElement;
      container.style.position = "relative";
      container.appendChild(customDropdown);
    };

    // Handle position checkbox changes
    positionCheckboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", () => {
        const role = getSelectedRole();
        if (role) {
          // Clear invalid selections
          Array.from(matchesSelect.options).forEach((option) => {
            if (option.dataset.role === role && option.selected) {
              option.selected = false;
            }
          });
          renderPills(role);
        }
        closeDropdown();
      });
    });

    // Handle dropdown trigger click
    dropdownTrigger.addEventListener("click", (e) => {
      e.preventDefault();
      if (customDropdown) {
        closeDropdown();
      } else {
        openDropdown();
      }
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", (e) => {
      if (customDropdown && !customDropdown.contains(e.target) && e.target !== dropdownTrigger) {
        closeDropdown();
      }
    });

  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPillbox);
  } else {
    initPillbox();
  }
})();
