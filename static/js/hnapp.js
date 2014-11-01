
init();



function init()
{
	// Auto-focus query field
	elById('header__searchbox__input').focus();
	
	// Enable toggle of syntax panel
	document.getElementById('syntax__toggle').onclick = function()
	{
		if (elById('syntax__content').style.display == 'block')
		{
			elById('syntax__content').style.display = 'none';
			window.location.hash = '';
		}
		else
		{
			elById('syntax__content').style.display = 'block';
			window.location.hash = '#showsyntax';
		}
		return false;
	}
	
	// Show syntax panel on page load
	if (window.location.hash === '#showsyntax')
	{
		elById('syntax__content').style.display = 'block';
	}
}


function elById(el_id)
{
	return document.getElementById(el_id);
}


