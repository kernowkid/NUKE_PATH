import nuke
import nukescripts

def copyWithInputs():
    n = nuke.selectedNodes() 
    [i['selected'].setValue(False) for i in nuke.allNodes()] #deselect all nodes
    cn = []
    
    #create copy of nodes and add their names to cn list
    for i in n:
        i['selected'].setValue(True)
        nukescripts.node_copypaste()
        p = nuke.selectedNode()
        p['xpos'].setValue(i['xpos'].value()+100)
        p['ypos'].setValue(i['ypos'].value()+50)
        p['selected'].setValue(False)
        cn.append( p['name'].value() )
    #cnr = cn[::-1]
    
    #loop thu cn list and match inputs to orig nodes
    counter = 0 
    for i in cn:
        nn = nuke.toNode(i)
        ln = n[counter]
        for r in range( ln.inputs() ):
            nn.setInput(r, ln.input(r) )        
            
        nn['selected'].setValue(True)
        counter = counter +1
            


def copyWithInputs_old():
    n = nuke.selectedNode()
    nukescripts.node_copypaste()
    cp = nuke.selectedNode()
    cp['xpos'].setValue(cp['xpos'].value()+50)
    cp['ypos'].setValue(cp['ypos'].value()+25)
    for r in range(n.inputs()):
        cp.setInput(r, n.input(r))
        

def copyWithInputs_old2():
    n = nuke.selectedNodes()
    if len(n) > 1:  #select multiple nodes in separate branches
        
        [i['selected'].setValue(False) for i in nuke.allNodes()]
        cn = []
        
        #create copy of nodes and add thier names to cn list
        for i in n:
            i['selected'].setValue(True)
            nukescripts.node_copypaste()
            p = nuke.selectedNode()
            p['xpos'].setValue(i['xpos'].value()+100)
            p['ypos'].setValue(i['ypos'].value()+50)
            p['selected'].setValue(False)
            cn.append( p['name'].value() )
        #cnr = cn[::-1]
        
        #loop thu cn list and match inputs to orig nodes
        counter = 0 
        for i in cn:
            nn = nuke.toNode(i)
            ln = n[counter]
            for r in range( ln.inputs() ):
                nn.setInput(r, ln.input(r) )        
                
            nn['selected'].setValue(True)
            counter = counter +1
                
    else: #select single node
        nukescripts.node_copypaste()
        cp = nuke.selectedNode()
        cp['xpos'].setValue(cp['xpos'].value()+50)
        cp['ypos'].setValue(cp['ypos'].value()+25)
        for r in range(n[0].inputs()):
            cp.setInput(r, n[0].input(r))
