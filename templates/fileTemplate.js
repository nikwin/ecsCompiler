var PARAMETERS = {parameters};

var allArgs = {allArgs};

var ecs = {{
{ecsList}
}};

{quotedLines}

var csvIdentifiers = {csvIdentifiers}

var findKeyFor = function(csvId, key, val){{
    return _.chain(csvIdentifiers[csvId])
    .filter(function(argKey){{
        return (allArgs[argKey][key] == val);
    }})
    .first()
    .value();
}};

var updateArgs = function(args, defaultArgs){{
    _.each(defaultArgs, function(val, key){{
        if (args[key] !== undefined){{
            console.log('overlapping value ' + key + ' ' + val);
        }}
        args[key] = val;
    }});
}};

var uidManager = (function(){{
    var uid = 0;
    return {{
        getUid: function(){{
            uid += 1;
            return uid;
        }},
        setUid: function(newUid){{
            uid = newUid;
        }}
    }};
}})();

var makeEcs = function(key, args){{
    args = (args === undefined) ? {{}} : args;
    args.uid = uidManager.getUid();
    if (ecs[key] === undefined){{
        console.log('tried to build ' + key);
    }}
    return ecs[key](args);
}};

var makeAllEcs = function(csvId){{
    return _.map(csvIdentifiers[csvId], function(key){{
        return makeEcs(key, {{}});
    }});
}};
