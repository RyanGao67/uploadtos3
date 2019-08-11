import React from 'react';
class Fileupload extends React.Component{
    constructor(props){
        super(props);
        this.state = {}
    }

    handleUpload = (ev)=>{
        ev.preventDefault();
        const data = new FormData();
        data.append('uploaded', this.uploadInput.files[0]);
        data.append('project_name', this.project.value);

        fetch("http://127.0.0.1:5000/upload",{
            method:"POST",
            body:data
        }).then((response)=>{
            console.log(response);
        })
    }

    render(){
        return <form >
            <div>
                <div>
                    <input ref = {(ref)=>{this.uploadInput = ref;} } type="file"/>
                </div>
                <div>
                    <input ref = {(ref)=>{this.project = ref;} } type="text" placeholder="project"/>
                </div>
                <div><button onClick={this.handleUpload}>UPLOAD</button></div>
            </div>
        </form>
    }
}


export default Fileupload;