
init();



function init()
{
	// Auto-focus query field
	elById('query').focus();
	
	// Enable toggle of syntax panel
	document.getElementById('syntax_toggle').onclick = function()
	{
		if (elById('syntax').style.display == 'block')
		{
			elById('syntax').style.display = 'none';
			window.location.hash = '';
		}
		else
		{
			elById('syntax').style.display = 'block';
			window.location.hash = '#showsyntax';
		}
		return false;
	}
	
	// Open syntax panel if requested
	if (window.location.hash === '#showsyntax')
	{
		elById('syntax').style.display = 'block';
	}
}


function elById(el_id)
{
	return document.getElementById(el_id);
}


